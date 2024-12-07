import os
import tempfile
import logging
import shutil
from typing import Optional
from cdktf import App, TerraformStack

logger = logging.getLogger(__name__)

class CDKTFHandler:
    def synthesize(self, cdktf_code: str) -> Optional[str]:
        """
        Synthesize CDKTF code into Terraform configuration
        
        Args:
            cdktf_code: String containing the CDKTF code
            
        Returns:
            Path to the synthesized output directory
        """
        temp_dir = None
        try:
            logger.info("Starting CDKTF synthesis")
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            logger.debug(f"Created temporary directory: {temp_dir}")
            
            # Create a memory namespace for the module
            namespace = {}
            exec(cdktf_code, namespace)
            
            # Create App and synthesize
            app = App(outdir=os.path.join(temp_dir, "cdktf.out"))
            if "MyStack" in namespace:
                stack = namespace["MyStack"](app, "my-stack")
                app.synth()
                
                synth_dir = os.path.join(temp_dir, "cdktf.out")
                if os.path.exists(synth_dir):
                    logger.debug(f"Successfully synthesized to: {synth_dir}")
                    return synth_dir
                else:
                    logger.error("Synthesis directory not found")
                    return None
            else:
                logger.error("No MyStack class found in CDKTF code")
                return None

        except Exception as e:
            logger.error(f"Error during CDKTF synthesis: {str(e)}")
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up temporary directory: {str(cleanup_error)}")
            return None
