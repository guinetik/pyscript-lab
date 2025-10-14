"""
Text Encoding & Hashing Utilities

Demonstrates PyScriptManager with multiple encoding/hashing functions.
Shows Python's "batteries included" advantage over JavaScript for crypto operations.

Supports:
- MD5 hash
- SHA-256 hash
- Base64 encoding/decoding
- ROT13 cipher

Author: Guinetik
"""

import hashlib
import base64
import codecs
from lib.pyscript_manager import PyScriptManager

# Initialize manager with module name
manager = PyScriptManager('encoder')

try:
    def encode_md5(text: str) -> str:
        """
        Generate MD5 hash of input text.

        Args:
            text: Input string to hash

        Returns:
            Hexadecimal MD5 hash string
        """
        if not text:
            return ""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def encode_sha256(text: str) -> str:
        """
        Generate SHA-256 hash of input text.

        Args:
            text: Input string to hash

        Returns:
            Hexadecimal SHA-256 hash string
        """
        if not text:
            return ""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def encode_base64(text: str) -> str:
        """
        Encode text to Base64.

        Args:
            text: Input string to encode

        Returns:
            Base64 encoded string
        """
        if not text:
            return ""
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')

    def decode_base64(text: str) -> str:
        """
        Decode Base64 text.

        Args:
            text: Base64 encoded string

        Returns:
            Decoded string or error message
        """
        if not text:
            return ""
        try:
            return base64.b64decode(text.encode('utf-8')).decode('utf-8')
        except Exception as e:
            return f"Error: Invalid Base64 - {str(e)}"

    def encode_rot13(text: str) -> str:
        """
        Apply ROT13 cipher to text.

        Args:
            text: Input string to encode

        Returns:
            ROT13 encoded string
        """
        if not text:
            return ""
        return codecs.encode(text, 'rot13')

    def encode_sha1(text: str) -> str:
        """
        Generate SHA-1 hash of input text.

        Args:
            text: Input string to hash

        Returns:
            Hexadecimal SHA-1 hash string
        """
        if not text:
            return ""
        return hashlib.sha1(text.encode('utf-8')).hexdigest()

    # Export all encoding functions and signal ready
    manager.signal_ready({
        'encodeMD5': encode_md5,
        'encodeSHA256': encode_sha256,
        'encodeSHA1': encode_sha1,
        'encodeBase64': encode_base64,
        'decodeBase64': decode_base64,
        'encodeROT13': encode_rot13
    })

    print("🔐 Encoder module ready with 6 encoding functions")

except Exception as e:
    manager.signal_error(e)
