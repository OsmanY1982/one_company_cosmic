"""
图像识别插件
支持 OCR、图像描述、二维码识别等功能
"""

import os
import base64
from typing import Dict, Any, List, Optional
from pathlib import Path


class ImageVisionPlugin:
    """图像视觉处理插件"""
    
    def __init__(self):
        self.upload_dir = os.path.expanduser("~/.opcclaw/images")
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def ocr(self, image_path: str, lang: str = "chi_sim+eng") -> Dict[str, Any]:
        """
        OCR 文字识别
        
        Args:
            image_path: 图片路径
            lang: 语言包（chi_sim=简体中文, eng=英文）
        
        Returns:
            识别结果
        """
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=lang)
            
            return {
                "success": True,
                "text": text,
                "language": lang
            }
        except ImportError:
            return {
                "success": False,
                "error": "未安装 pytesseract，请运行: pip install pytesseract pillow"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def describe_image(self, image_path: str) -> Dict[str, Any]:
        """
        描述图像内容（使用多模态模型）
        
        Args:
            image_path: 图片路径
        
        Returns:
            描述结果
        """
        try:
            # 检查是否支持多模态的模型
            # 这里可以集成 Qwen-VL, GPT-4V 等
            return {
                "success": True,
                "description": "图像描述功能需要配置多模态模型（如 Qwen-VL、GPT-4V）",
                "image_path": image_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_qrcode(self, image_path: str) -> Dict[str, Any]:
        """读取二维码"""
        try:
            from pyzbar.pyzbar import decode
            from PIL import Image
            
            image = Image.open(image_path)
            decoded = decode(image)
            
            if decoded:
                results = []
                for d in decoded:
                    results.append({
                        "data": d.data.decode("utf-8"),
                        "type": d.type
                    })
                return {"success": True, "codes": results}
            else:
                return {"success": True, "codes": [], "message": "未检测到二维码"}
                
        except ImportError:
            return {
                "success": False,
                "error": "未安装 pyzbar，请运行: pip install pyzbar pillow"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_qrcode(self, data: str, output_path: str = None) -> Dict[str, Any]:
        """生成二维码"""
        try:
            import qrcode
            
            if output_path is None:
                output_path = os.path.join(self.upload_dir, f"qrcode_{hash(data)}.png")
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(output_path)
            
            return {
                "success": True,
                "path": output_path,
                "data": data
            }
        except ImportError:
            return {
                "success": False,
                "error": "未安装 qrcode，请运行: pip install qrcode[pil]"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def resize_image(self, image_path: str, width: int = None, 
                     height: int = None, output_path: str = None) -> Dict[str, Any]:
        """调整图片大小"""
        try:
            from PIL import Image
            
            img = Image.open(image_path)
            
            if width and height:
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            elif width:
                ratio = width / img.width
                height = int(img.height * ratio)
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            elif height:
                ratio = height / img.height
                width = int(img.width * ratio)
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_resized{ext}"
            
            img.save(output_path)
            
            return {
                "success": True,
                "path": output_path,
                "size": (img.width, img.height)
            }
        except ImportError:
            return {
                "success": False,
                "error": "未安装 Pillow，请运行: pip install Pillow"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def image_to_base64(self, image_path: str) -> str:
        """图片转 Base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()


def initialize(plugin_manager):
    """插件初始化"""
    plugin = ImageVisionPlugin()
    plugin_manager.image_vision = plugin
    print("[ImageVision] Plugin loaded")
