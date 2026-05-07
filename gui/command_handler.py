from typing import Dict, List


class CommandHandler:
    """Handles TFT game command processing"""

    def __init__(self, logger, commands: Dict[str, List[str]] = None, descriptions: Dict[str, str] = None):
        """Initialize command handler

        Args:
            logger: DebugLogger instance
            commands: Dict mapping action_name -> list of trigger phrases
            descriptions: Dict mapping action_name -> human-readable description
        """
        self.logger = logger
        self.commands = commands or {}
        self.descriptions = descriptions or {}

    def process_command(self, command: str) -> dict:
        """Process command and return action info

        Args:
            command: Command string

        Returns:
            Dict with action and parameters
        """
        command = command.lower().strip()

        # Detect action
        action = None
        for action_name, keywords in self.commands.items():
            if any(keyword in command for keyword in keywords):
                action = action_name
                break

        if action:
            self.logger.log("ACTION", f"Command detected: {action}")
            return {'action': action, 'command': command}
        else:
            self.logger.log("WARNING", f"Unknown command: {command}")
            return {'action': None, 'command': command}

    def get_action_description(self, action: str) -> str:
        """Get human-readable action description

        Args:
            action: Action name

        Returns:
            Description string
        """
        return self.descriptions.get(action, 'Unknown command')
