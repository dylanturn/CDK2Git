import os
import logging
import hashlib
import struct
import zlib
import shutil
from typing import Dict, List, Optional, Tuple
from cdktf_handler import CDKTFHandler

logger = logging.getLogger(__name__)

class GitHandler:
    def __init__(self):
        self.project_path = None
        self.cdktf_handler = CDKTFHandler()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def set_project_path(self, project_path: str):
        """Set the current project path"""
        self.project_path = project_path
        logger.debug(f"Set project path to: {project_path}")

    def get_project_dir(self) -> str:
        """Get the absolute path to the project directory"""
        project_dir = os.path.join(self.base_dir, self.project_path)
        logger.debug(f"Base dir: {self.base_dir}")
        logger.debug(f"Project path: {self.project_path}")
        logger.debug(f"Full project dir: {project_dir}")
        return project_dir

    def create_blob(self, content: str) -> Tuple[str, bytes]:
        """Create a Git blob object from content"""
        data = content.encode('utf-8')
        blob_store = b'blob ' + str(len(data)).encode('utf-8') + b'\x00' + data
        blob_hash = hashlib.sha1(blob_store).hexdigest()
        
        return blob_hash, blob_store

    def create_tree(self, objects: List[Tuple[str, str, bytes]]) -> Tuple[str, bytes]:
        """Create a Git tree object from a list of (path, hash, blob) tuples"""
        # Sort objects by path for consistent ordering
        sorted_objects = sorted(objects, key=lambda x: x[0])
        
        # Build tree content
        tree_content = bytearray()
        for path, hash_value, _ in sorted_objects:
            # Mode (100644 for files)
            mode = b'100644'
            # Null byte separator
            tree_content.extend(mode + b' ' + path.encode('utf-8') + b'\x00')
            # Add 20-byte hash
            tree_content.extend(bytes.fromhex(hash_value))
        
        # Create tree object
        tree_data = bytes(tree_content)
        tree_store = b'tree ' + str(len(tree_data)).encode('utf-8') + b'\x00' + tree_data
        tree_hash = hashlib.sha1(tree_store).hexdigest()
        
        return tree_hash, tree_store

    def create_commit(self, tree_hash: str) -> Tuple[str, bytes]:
        """Create a Git commit object"""
        # Build commit content
        commit_content = [
            f'tree {tree_hash}',
            'author CDK2Git <cdk2git@example.com> 1701926400 +0000',
            'committer CDK2Git <cdk2git@example.com> 1701926400 +0000',
            '',
            'Initial commit - CDKTF synthesis output'
        ]
        commit_data = '\n'.join(commit_content).encode('utf-8')
        
        # Create commit object
        commit_store = b'commit ' + str(len(commit_data)).encode('utf-8') + b'\x00' + commit_data
        commit_hash = hashlib.sha1(commit_store).hexdigest()
        
        return commit_hash, commit_store

    def create_packfile(self, objects: List[Tuple[str, bytes]]) -> bytes:
        """Create a Git packfile containing the given objects"""
        # Pack header: 'PACK' + version(=2) + number of objects
        header = b'PACK' + struct.pack('>II', 2, len(objects))
        
        # Pack data
        data = bytearray()
        for obj_hash, content in objects:
            # Determine object type
            if content.startswith(b'commit '):
                obj_type = 1
            elif content.startswith(b'tree '):
                obj_type = 2
            else:
                obj_type = 3  # blob
            
            # Get the actual content (after header)
            null_pos = content.find(b'\x00')
            if null_pos != -1:
                content = content[null_pos + 1:]
            
            # Compress the content
            compressed = zlib.compress(content)
            
            # Object header: type and size
            size = len(content)
            c = (obj_type << 4) | (size & 0x0f)
            size >>= 4
            while size > 0:
                data.append(0x80 | c)
                c = size & 0x7f
                size >>= 7
            data.append(c)
            
            # Add compressed content
            data.extend(compressed)
        
        # Calculate pack checksum
        pack = header + bytes(data)
        sha1_hash = hashlib.sha1(pack).digest()
        
        # Return pack with checksum
        return pack + sha1_hash

    def parse_request(self, data: bytes) -> List[str]:
        """Parse Git client request data"""
        wants = []
        logger.debug(f"Parsing request data: {data!r}")
        
        # Git request data is in pkt-line format
        pos = 0
        while pos < len(data):
            # Read length (4 hex digits)
            try:
                length = int(data[pos:pos + 4].decode('ascii'), 16)
                logger.debug(f"Packet length: {length}")
                
                if length == 0:
                    # Flush packet
                    pos += 4
                    continue
                
                # Read packet content
                packet = data[pos + 4:pos + length]
                logger.debug(f"Packet content: {packet!r}")
                
                if packet.startswith(b'want '):
                    wants.append(packet[5:45].decode('ascii'))
                    logger.debug(f"Found want: {wants[-1]}")
                
                pos += length
                
            except Exception as e:
                logger.error(f"Error parsing packet at position {pos}: {str(e)}")
                break
        
        logger.debug(f"Parsed wants: {wants}")
        return wants

    def format_side_band(self, data: bytes, band: int = 1) -> bytes:
        """Format data with side-band encoding"""
        # band 1: pack data
        # band 2: progress messages
        # band 3: error messages
        result = bytearray()
        chunk_size = 65519  # 64KB minus overhead
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            # Format: [len][band][data]
            length = len(chunk) + 5  # 4 bytes for length + 1 byte for band
            result.extend(f"{length:04x}".encode('ascii'))
            result.append(band)
            result.extend(chunk)
        
        # Add flush packet
        result.extend(b"0000")
        return bytes(result)

    def format_pack_response(self, pack_data: bytes) -> bytes:
        """Format pack data according to Git protocol with side-band"""
        # First send NAK to end negotiation
        response = bytearray()
        
        # NAK in pkt-line format
        nak = b"NAK\n"
        response.extend(f"{len(nak) + 4:04x}".encode('ascii'))
        response.extend(nak)
        
        # Then send pack data in side-band mode
        response.extend(self.format_side_band(pack_data))
        
        logger.debug(f"Response starts with: {bytes(response[:32])!r}")
        return bytes(response)

    def get_refs(self) -> bytes:
        """Generate Git references advertisement"""
        # Get the latest commit hash from synthesized data
        synth_dir = None
        try:
            # Read and synthesize to get the commit hash
            project_dir = self.get_project_dir()
            main_py_path = os.path.join(project_dir, 'main.py')
            
            with open(main_py_path, 'r') as f:
                cdktf_code = f.read()

            synth_dir = self.cdktf_handler.synthesize(cdktf_code)
            if not synth_dir:
                commit_hash = "0" * 40
            else:
                # Create tree and commit
                objects = []
                for root, _, files in os.walk(synth_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r') as f:
                            content = f.read()
                        rel_path = os.path.relpath(file_path, synth_dir)
                        hash_value, blob = self.create_blob(content)
                        objects.append((rel_path, hash_value, blob))

                if objects:
                    tree_hash, _ = self.create_tree(objects)
                    commit_hash, _ = self.create_commit(tree_hash)
                else:
                    commit_hash = "0" * 40

        except Exception as e:
            logger.error(f"Error generating refs: {str(e)}")
            commit_hash = "0" * 40
            
        finally:
            if synth_dir and os.path.exists(synth_dir):
                try:
                    shutil.rmtree(synth_dir)
                except Exception as e:
                    logger.error(f"Error cleaning up synthesis directory: {str(e)}")
        
        # Format according to Git protocol
        # First packet: service announcement
        service = "# service=git-upload-pack\n"
        first_pkt = f"{len(service) + 4:04x}{service}"
        
        # Second packet: flush
        second_pkt = "0000"
        
        # Third packet: HEAD symref with capabilities
        capabilities = "multi_ack thin-pack side-band side-band-64k ofs-delta shallow deepen-since deepen-not deepen-relative no-progress include-tag multi_ack_detailed symref=HEAD:refs/heads/main agent=git/2.43.0"
        head_line = f"{commit_hash} HEAD\0{capabilities}\n"
        third_pkt = f"{len(head_line) + 4:04x}{head_line}"
        
        # Fourth packet: main branch ref
        main_line = f"{commit_hash} refs/heads/main\n"
        fourth_pkt = f"{len(main_line) + 4:04x}{main_line}"
        
        # Final packet: flush
        final_pkt = "0000"
        
        return (first_pkt + second_pkt + third_pkt + fourth_pkt + final_pkt).encode('utf-8')

    def generate_pack(self, request_data: bytes) -> Optional[bytes]:
        """Generate Git packfile in response to client request"""
        # Parse client's wants
        wants = self.parse_request(request_data)
        if not wants:
            logger.error("No wants in client request")
            return None

        synth_dir = None
        try:
            # Read the project's main.py
            project_dir = self.get_project_dir()
            main_py_path = os.path.join(project_dir, 'main.py')
            
            logger.debug(f"Looking for main.py at: {main_py_path}")
            if not os.path.exists(main_py_path):
                logger.error(f"main.py not found at: {main_py_path}")
                return None
            
            with open(main_py_path, 'r') as f:
                cdktf_code = f.read()

            # Synthesize the CDKTF code
            synth_dir = self.cdktf_handler.synthesize(cdktf_code)
            if not synth_dir:
                logger.error("Failed to synthesize CDKTF code")
                return None

            # Create Git objects from synthesized files
            objects = []
            for root, _, files in os.walk(synth_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Create relative path from synth_dir
                    rel_path = os.path.relpath(file_path, synth_dir)
                    hash_value, blob = self.create_blob(content)
                    objects.append((rel_path, hash_value, blob))

            if not objects:
                logger.error("No files found in synthesis output")
                return None

            # Create tree object
            tree_hash, tree_content = self.create_tree(objects)
            
            # Create commit object
            commit_hash, commit_content = self.create_commit(tree_hash)
            
            # Generate pack data with all objects
            pack_objects = [(hash_value, blob) for _, hash_value, blob in objects]
            pack_objects.append((tree_hash, tree_content))
            pack_objects.append((commit_hash, commit_content))
            
            # Sort objects to ensure consistent order
            pack_objects.sort(key=lambda x: x[0])
            
            # Generate pack data
            pack_data = self.create_packfile(pack_objects)

            # Format response according to Git protocol
            return self.format_pack_response(pack_data)

        except Exception as e:
            logger.error(f"Error generating pack data: {str(e)}", exc_info=True)
            return None
            
        finally:
            # Only cleanup after we've generated the pack data
            if synth_dir and os.path.exists(synth_dir):
                try:
                    import shutil
                    shutil.rmtree(synth_dir)
                except Exception as e:
                    logger.error(f"Error cleaning up synthesis directory: {str(e)}")
