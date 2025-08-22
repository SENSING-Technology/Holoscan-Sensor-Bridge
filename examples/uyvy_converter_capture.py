import holoscan
import numpy as np

class UYVYToRGBOperator(holoscan.core.Operator):
    def setup(self, spec):
        spec.input("input")
        spec.output("output")
        self.frame_count = 0
    
    def compute(self, op_input, op_output, context):
        try:
            # Receive UYVY data
            uyvy_data = op_input.receive("input")
            self.frame_count += 1
            
            # Correctly extract Tensor data from dictionary
            if isinstance(uyvy_data, dict):
                if len(uyvy_data) > 0:
                    first_key = list(uyvy_data.keys())[0]  # Usually ''
                    actual_data = uyvy_data[first_key]
                    if hasattr(actual_data, 'asnumpy'):
                        uyvy_np = actual_data.asnumpy()
                    else:
                        uyvy_np = np.asarray(actual_data)
                else:
                    uyvy_np = np.zeros(1920*1536*2, dtype=np.uint8)
            else:
                if hasattr(uyvy_data, 'asnumpy'):
                    uyvy_np = uyvy_data.asnumpy()
                else:
                    uyvy_np = np.asarray(uyvy_data)
            
            print(f"Frame {self.frame_count}: Processing UYVY data {uyvy_np.shape}")
            
            # UYVY to RGBA conversion - stable version
            rgba_np = self.uyvy_to_rgba(uyvy_np)
            
            # Ensure correct data type
            if rgba_np.dtype != np.uint8:
                rgba_np = rgba_np.astype(np.uint8)
            
            print(f"Frame {self.frame_count}: Output RGBA image {rgba_np.shape}")
            op_output.emit(rgba_np, "output")
            
        except Exception as e:
            print(f"UYVY conversion error: {e}")
            import traceback
            traceback.print_exc()
            # Send test image as fallback
            test_img = np.zeros((1536, 1920, 4), dtype=np.uint8)
            test_img[:, :, 0] = 255  # Red
            test_img[:, :, 3] = 255  # Alpha
            op_output.emit(test_img, "output")
    
    def uyvy_to_rgba(self, uyvy_data):
        """UYVY to RGBA conversion - stable version"""
        try:
            uyvy_flat = uyvy_data.flatten()
            expected_size = 1920 * 1536 * 2
            if uyvy_flat.size != expected_size:
                print(f"Data size mismatch: expected {expected_size}, actual {uyvy_flat.size}")
                if uyvy_flat.size > expected_size:
                    uyvy_flat = uyvy_flat[:expected_size]
                else:
                    return np.zeros((1536, 1920, 4), dtype=np.uint8)
            
            # Reshape into row format
            uyvy_reshaped = uyvy_flat.reshape(1536, 1920 * 2)
            
            # Extract components (UYVY format: U0 Y0 V0 Y1 U2 Y2 V2 Y3 ...)
            u = uyvy_reshaped[:, 0::4].astype(np.float32)    # U component
            y0 = uyvy_reshaped[:, 1::4].astype(np.float32)   # First Y component
            v = uyvy_reshaped[:, 2::4].astype(np.float32)    # V component
            y1 = uyvy_reshaped[:, 3::4].astype(np.float32)   # Second Y component
            
            # Expand U and V values
            u_expanded = np.repeat(u, 2, axis=1)
            v_expanded = np.repeat(v, 2, axis=1)
            
            # Construct full Y component
            y_expanded = np.zeros((1536, 1920), dtype=np.float32)
            y_expanded[:, 0::2] = y0
            y_expanded[:, 1::2] = y1
            
            # YUV to RGB conversion (try different coefficient combinations)
            r = np.clip(y_expanded + 1.402 * (v_expanded - 128), 0, 255)      # Use V
            g = np.clip(y_expanded - 0.344136 * (u_expanded - 128) - 0.714136 * (v_expanded - 128), 0, 255)  # Use U and V
            b = np.clip(y_expanded + 1.772 * (u_expanded - 128), 0, 255)      # Use U
            
            # Combine RGBA values
            rgba = np.zeros((1536, 1920, 4), dtype=np.uint8)
            rgba[:, :, 0] = r.astype(np.uint8)  # R
            rgba[:, :, 1] = g.astype(np.uint8)  # G
            rgba[:, :, 2] = b.astype(np.uint8)  # B
            rgba[:, :, 3] = 255                 # Alpha
            
            return rgba
            
        except Exception as e:
            print(f"Conversion error: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros((1536, 1920, 4), dtype=np.uint8)