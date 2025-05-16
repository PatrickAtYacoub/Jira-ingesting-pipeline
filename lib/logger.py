import logging
import os
from .project_path import SystemPath

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Configure file handler for logging
log_file_path = os.path.join(SystemPath.absolute('[]'), "pipeline.log")
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# === agent_logger ===

agent_logger = logging.getLogger("agent_logger")
agent_logger.setLevel(logging.INFO)
# Configure file handler for agent_logger
agent_log_file_path = os.path.join(SystemPath.absolute('[]'), "agent.log")
agent_file_handler = logging.FileHandler(agent_log_file_path)
agent_file_handler.setLevel(logging.INFO)
agent_file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
agent_file_handler.setFormatter(agent_file_formatter)
agent_logger.addHandler(agent_file_handler)
