import cv2
import socket
import threading
import time
import asyncio
import numpy as np
from typing import Optional, Callable, Tuple, Awaitable
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import logging

logger = logging.getLogger(__name__)

try:
    from turbojpeg import TurboJPEG, TJPF_BGR
    _jpeg = TurboJPEG()
except Exception:
    _jpeg = None


class OBS_UDP_Receiver(threading.Thread):
    """
    OBS UDP receiver for MJPEG stream from OBS Studio
    Supports receiving Motion JPEG stream over UDP protocol
    """
    
    def __init__(self, ip: str = "0.0.0.0", port: int = 1234, target_fps: int = 60, max_workers: int = None):
        threading.Thread.__init__(self, daemon=True, name=f"OBS_UDP_Receiver-{port}")
        
        ip = "0.0.0.0"
        
        self.ip = ip
        self.port = port
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps if target_fps > 0 else 0
        
        self.socket = None
        self.is_connected = False
        self.is_receiving = False
        self.thread_started = False
        
        self.stop_event = threading.Event()
        self._loop = None
        self._loop_thread = None
        self._transport = None
        self._protocol = None
        
        self.max_workers = max_workers if max_workers is not None else min(8, (threading.active_count() or 1) + 4)
        self.executor = None
        self.frame_queue = Queue(maxsize=100)
        self.processing_lock = threading.Lock()
        
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.frame_callback = None
        self.frame_callback_async: Optional[Callable[[np.ndarray], Awaitable[None]]] = None
        
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        self.processing_fps = 0.0
        self.last_processing_time = time.time()
        self.processing_counter = 0
        self.receive_delay = 0.0
        self.processing_delay = 0.0
        self.decoding_fps = 0.0
        self.decoding_counter = 0
        self.last_decoding_time = time.time()
        
        self.mjpeg_buffer = bytearray()
        self.buffer_lock = threading.Lock()
        self.mjpeg_start_marker = b'\xff\xd8'
        self.mjpeg_end_marker = b'\xff\xd9'
        self.max_buffer_size = 2 * 1024 * 1024
        
        self.packet_count = 0
        self.invalid_header_count = 0
        self.decode_error_count = 0
        
        logger.info(f"OBS_UDP_Receiver initialized: {ip}:{port}, max_workers={self.max_workers}")
    
    def run(self):
        self._receive_loop()
    
    def set_frame_callback(self, callback: Callable[[np.ndarray], None]):
        self.frame_callback = callback
    
    def set_frame_callback_async(self, callback: Callable[[np.ndarray], Awaitable[None]]):
        self.frame_callback_async = callback
    
    def connect(self) -> bool:
        try:
            if self.is_connected:
                self.disconnect()
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
            self.socket.settimeout(1.0)
            
            self.socket.bind((self.ip, self.port))
            
            self.is_connected = True
            self.stop_event.clear()
            
            threading.Thread.start(self)
            self.thread_started = True
            
            time.sleep(0.1)
            
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="FrameDecoder")
            
            self.processing_thread = threading.Thread(target=self._frame_processing_loop, daemon=True, name=f"FrameProcessor-{self.port}")
            self.processing_thread.start()
            
            logger.info(f"Connected to UDP stream at {self.ip}:{self.port}")
            return True
            
        except OSError as e:
            logger.error(f"Failed to connect to UDP stream: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to UDP stream: {e}")
            self.is_connected = False
            return False

    class _UDPProtocol(asyncio.DatagramProtocol):
        def __init__(self, receiver: "OBS_UDP_Receiver"):
            self.receiver = receiver

        def datagram_received(self, data: bytes, addr):
            receive_time = time.time()
            try:
                self.receiver._process_mjpeg_data(data, receive_time)
            except Exception as e:
                logger.error(f"Protocol datagram handling error: {e}", exc_info=True)

        def error_received(self, exc):
            logger.error(f"UDP error received: {exc}")

    def _ensure_loop_thread(self):
        if self._loop and self._loop_thread and self._loop_thread.is_alive():
            return
        self._loop = asyncio.new_event_loop()
        def run_loop(loop: asyncio.AbstractEventLoop):
            asyncio.set_event_loop(loop)
            loop.run_forever()
        self._loop_thread = threading.Thread(target=run_loop, args=(self._loop,), daemon=True)
        self._loop_thread.start()

    async def _connect_asyncio(self):
        if self.is_connected:
            await self._disconnect_asyncio()
        loop = asyncio.get_running_loop()
        listen = await loop.create_datagram_endpoint(
            lambda: OBS_UDP_Receiver._UDPProtocol(self),
            local_addr=(self.ip, self.port),
        )
        self._transport, self._protocol = listen
        self.is_connected = True
        self.is_receiving = True
        self.stop_event.clear()
        
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="FrameDecoder")
        
        if not hasattr(self, 'processing_thread') or not self.processing_thread.is_alive():
            self.processing_thread = threading.Thread(target=self._frame_processing_loop, daemon=True)
            self.processing_thread.start()
        
        logger.info(f"[async] Connected to UDP stream at {self.ip}:{self.port}")
        return True

    async def _disconnect_asyncio(self):
        try:
            self.is_receiving = False
            self.is_connected = False
            self.stop_event.set()
            
            if self.executor:
                self.executor.shutdown(wait=False, cancel_futures=True)
                self.executor = None
            
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except Exception:
                    break
            
            if self._transport is not None:
                self._transport.close()
                await asyncio.sleep(0.1)
                self._transport = None
            self._protocol = None
            
            if self._loop and self._loop_thread and self._loop_thread.is_alive():
                self._loop.call_soon_threadsafe(self._loop.stop)
                self._loop_thread.join(timeout=2.0)
                self._loop = None
                self._loop_thread = None
            
            logger.info("[async] Disconnected from UDP stream")
        except Exception as e:
            logger.error(f"[async] Error during disconnect: {e}", exc_info=True)

    def connect_async(self) -> bool:
        try:
            self._ensure_loop_thread()
            fut = asyncio.run_coroutine_threadsafe(self._connect_asyncio(), self._loop)
            return bool(fut.result(timeout=5.0))
        except asyncio.TimeoutError:
            logger.error("Async connect timeout")
            return False
        except Exception as e:
            logger.error(f"Failed to start async UDP receiver: {e}", exc_info=True)
            return False

    def disconnect_async(self):
        try:
            if self._loop:
                fut = asyncio.run_coroutine_threadsafe(self._disconnect_asyncio(), self._loop)
                try:
                    fut.result(timeout=3.0)
                except (asyncio.TimeoutError, Exception):
                    pass
        except Exception as e:
            logger.error(f"Error scheduling async disconnect: {e}", exc_info=True)
    
    def disconnect(self):
        try:
            self.is_connected = False
            self.is_receiving = False
            self.stop_event.set()
            
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=2.0)
            
            if self.executor:
                self.executor.shutdown(wait=False, cancel_futures=True)
                self.executor = None
            
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except Exception:
                    break
            
            if self.socket:
                self.socket.close()
                self.socket = None
            
            with self.buffer_lock:
                self.mjpeg_buffer.clear()
            
            with self.frame_lock:
                self.current_frame = None
            
            logger.info("Disconnected from UDP stream")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}", exc_info=True)
    
    def _receive_loop(self):
        self.is_receiving = True
        logger.info("Started UDP receive loop")
        
        while not self.stop_event.is_set() and self.is_connected:
            try:
                data, addr = self.socket.recvfrom(65536)
                receive_time = time.time()
                
                self.packet_count += 1
                self._process_mjpeg_data(data, receive_time)
                
            except socket.timeout:
                continue
            except OSError as e:
                if self.is_connected:
                    logger.error(f"Socket error in receive loop: {e}")
                break
            except Exception as e:
                if self.is_connected:
                    logger.error(f"Error in receive loop: {e}", exc_info=True)
                break
        
        self.is_receiving = False
        logger.info("UDP receive loop ended")
    
    def _frame_processing_loop(self):
        logger.info("Started frame processing loop")
        
        while not self.stop_event.is_set() and self.is_connected:
            try:
                try:
                    future, receive_time = self.frame_queue.get(timeout=0.1)
                    frame = future.result(timeout=1.0)
                    if frame is not None:
                        self._update_frame(frame, receive_time)
                except Exception:
                    continue
                    
            except Exception as e:
                if self.is_connected:
                    logger.error(f"Error in frame processing loop: {e}", exc_info=True)
                continue
        
        logger.info("Frame processing loop ended")
    
    def _process_mjpeg_data(self, data: bytes, receive_time: float):
        try:
            with self.buffer_lock:
                self.mjpeg_buffer.extend(data)
                
                buffer_len = len(self.mjpeg_buffer)
                if buffer_len > self.max_buffer_size:
                    self.mjpeg_buffer.clear()
                    return
                
                buffer = bytes(self.mjpeg_buffer)
            
            frames_processed = 0
            max_frames_per_packet = 5
            bytes_removed_from_start = 0
            
            while frames_processed < max_frames_per_packet:
                start_pos = buffer.find(self.mjpeg_start_marker)
                if start_pos == -1:
                    if len(buffer) > 2048:
                        with self.buffer_lock:
                            if len(self.mjpeg_buffer) > 1024:
                                self.mjpeg_buffer = self.mjpeg_buffer[-1024:]
                    break
                
                if start_pos > 0:
                    bytes_removed_from_start += start_pos
                    buffer = buffer[start_pos:]
                
                end_pos = buffer.find(self.mjpeg_end_marker, 2)
                if end_pos == -1:
                    break
                
                jpeg_data = buffer[:end_pos + 2]
                frame_end_pos = end_pos + 2
                
                bytes_removed_from_start += frame_end_pos
                buffer = buffer[frame_end_pos:]
                
                if len(jpeg_data) < 100:
                    continue
                
                if len(jpeg_data) > 10 * 1024 * 1024:
                    continue
                
                if self.executor and not self.stop_event.is_set():
                    future = self.executor.submit(self._decode_jpeg_frame, jpeg_data, receive_time)
                    try:
                        if self.frame_queue.full():
                            self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait((future, receive_time))
                    except Exception:
                        pass
                    frames_processed += 1
            
            if bytes_removed_from_start > 0:
                with self.buffer_lock:
                    if bytes_removed_from_start <= len(self.mjpeg_buffer):
                        self.mjpeg_buffer = self.mjpeg_buffer[bytes_removed_from_start:]
                
        except Exception as e:
            logger.error(f"Error processing MJPEG data: {e}", exc_info=True)
            with self.buffer_lock:
                self.mjpeg_buffer.clear()
    
    def _decode_jpeg_frame(self, jpeg_data: bytes, receive_time: float) -> Optional[np.ndarray]:
        try:
            if len(jpeg_data) < 100:
                return None
            
            if not jpeg_data.startswith(b'\xff\xd8') or not jpeg_data.endswith(b'\xff\xd9'):
                self.invalid_header_count += 1
                return None
            
            frame = None
            if _jpeg is not None:
                try:
                    frame = _jpeg.decode(jpeg_data, pixel_format=TJPF_BGR)
                    if frame is not None and frame.size > 0:
                        self.decoding_counter += 1
                        self.receive_delay = (time.time() - receive_time) * 1000
                        return frame
                except Exception:
                    self.decode_error_count += 1
            
            nparr = np.frombuffer(jpeg_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None or frame.size == 0:
                self.decode_error_count += 1
                return None
            
            if len(frame.shape) < 2 or frame.shape[0] <= 0 or frame.shape[1] <= 0:
                self.decode_error_count += 1
                return None
            
            height, width = frame.shape[:2]
            if height < 10 or width < 10 or height > 10000 or width > 10000:
                self.decode_error_count += 1
                return None
            
            if self._is_frame_corrupted(frame):
                self.decode_error_count += 1
                return None
            
            self.decoding_counter += 1
            self.receive_delay = (time.time() - receive_time) * 1000
            return frame
            
        except Exception as e:
            self.decode_error_count += 1
            return None
    
    @staticmethod
    def _is_frame_corrupted(frame: np.ndarray) -> bool:
        try:
            h, w = frame.shape[:2]
            sample_points = [
                frame[0, 0], frame[0, -1], frame[-1, 0], frame[-1, -1],
                frame[h//2, w//2]
            ]
            if len(set(tuple(sample) for sample in sample_points)) == 1:
                return True
            if all(np.all(sample == 0) for sample in sample_points):
                return True
            return False
        except Exception:
            return True
    
    def _update_frame(self, frame: np.ndarray, receive_time: float):
        try:
            with self.frame_lock:
                self.current_frame = frame.copy()
            
            with self.processing_lock:
                self.decoding_counter += 1
                current_time = time.time()
                if current_time - self.last_decoding_time >= 1.0:
                    self.decoding_fps = self.decoding_counter / (current_time - self.last_decoding_time)
                    self.decoding_counter = 0
                    self.last_decoding_time = current_time
            
            self._update_fps_counters()
            
            processing_start = time.time()
            if self.frame_callback_async and self._loop:
                try:
                    asyncio.run_coroutine_threadsafe(self.frame_callback_async(frame.copy()), self._loop)
                except Exception as e:
                    logger.error(f"Error scheduling async frame callback: {e}")
            if self.frame_callback:
                try:
                    if self.executor:
                        self.executor.submit(self.frame_callback, frame.copy())
                    else:
                        self.frame_callback(frame.copy())
                except Exception as e:
                    logger.error(f"Frame callback error: {e}", exc_info=True)
            processing_end = time.time()

            with self.processing_lock:
                self.processing_delay = (processing_end - processing_start) * 1000
                self.processing_counter += 1
                if processing_end - self.last_processing_time >= 1.0:
                    self.processing_fps = self.processing_counter / (processing_end - self.last_processing_time)
                    self.processing_counter = 0
                    self.last_processing_time = processing_end
            
        except Exception as e:
            logger.error(f"Error updating frame: {e}", exc_info=True)
    
    def _update_fps_counters(self):
        current_time = time.time()
        self.fps_counter += 1
        
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.last_fps_time)
            self.fps_counter = 0
            self.last_fps_time = current_time
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def get_performance_stats(self) -> dict:
        with self.buffer_lock:
            buffer_size = len(self.mjpeg_buffer)
        
        with self.processing_lock:
            processing_fps = self.processing_fps
            processing_delay = self.processing_delay
            decoding_fps = self.decoding_fps
        
        return {
            'current_fps': self.current_fps,
            'processing_fps': processing_fps,
            'decoding_fps': decoding_fps,
            'target_fps': self.target_fps,
            'receive_delay_ms': self.receive_delay,
            'processing_delay_ms': processing_delay,
            'is_connected': self.is_connected,
            'is_receiving': self.is_receiving,
            'buffer_size_bytes': buffer_size,
            'queue_size': self.frame_queue.qsize(),
            'max_workers': self.max_workers,
            'packet_count': self.packet_count,
            'invalid_header_count': self.invalid_header_count,
            'decode_error_count': self.decode_error_count
        }
    
    def set_target_fps(self, fps: int):
        self.target_fps = max(1, fps)
        self.frame_interval = 1.0 / self.target_fps if self.target_fps > 0 else 0
        logger.info(f"Target FPS set to {self.target_fps} (monitoring only, no limit enforced)")
    
    def update_connection_params(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        logger.info(f"Connection parameters updated: {ip}:{port}")


class OBS_UDP_Manager:
    """
    Manager class for OBS UDP connections
    Provides high-level interface for UDP stream management
    """
    
    def __init__(self):
        self.receiver = None
        self.is_connected = False
        
    def create_receiver(self, ip: str, port: int, target_fps: int = 60) -> OBS_UDP_Receiver:
        self.receiver = OBS_UDP_Receiver(ip, port, target_fps)
        return self.receiver
    
    def connect(self, ip: str, port: int, target_fps: int = 60) -> bool:
        if self.receiver:
            self.receiver.disconnect()
        
        self.receiver = OBS_UDP_Receiver(ip, port, target_fps)
        success = self.receiver.connect()
        self.is_connected = success
        return success

    def connect_async(self, ip: str, port: int, target_fps: int = 60) -> bool:
        if self.receiver:
            try:
                self.receiver.disconnect_async()
            except Exception:
                pass
        self.receiver = OBS_UDP_Receiver(ip, port, target_fps)
        success = self.receiver.connect_async()
        self.is_connected = success
        return success

    def disconnect_async(self):
        if self.receiver:
            self.receiver.disconnect_async()
            self.receiver = None
        self.is_connected = False
    
    def disconnect(self):
        if self.receiver:
            self.receiver.disconnect()
            self.receiver = None
        self.is_connected = False
    
    def get_receiver(self) -> Optional[OBS_UDP_Receiver]:
        return self.receiver
    
    def is_stream_active(self) -> bool:
        return self.is_connected and self.receiver and self.receiver.is_receiving
