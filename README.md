# MCP File Management Server

A Model Context Protocol (MCP) server that provides file and folder management capabilities for Claude Desktop and other MCP-compatible clients.

## Features

- **Create Folders**: Create directories with support for nested paths
- **Create Files**: Create empty files with automatic parent directory creation
- **List Contents**: Browse directory contents with file size information
- **Path Security**: Sandboxed operations within a designated base directory (Desktop by default)

## Project Structure

```
mcp-producer/
├── mcp_server.py           # Main MCP server implementation
├── mcp_manual_tester.py    # Interactive testing tool for MCP functions
├── claude_config.json      # Configuration for Claude Desktop
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd mcp-producer
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Claude Desktop** (optional):
   - Copy the configuration from `claude_config.json` to your Claude Desktop configuration
   - Update the paths in the configuration to match your system

## Usage

### Running the MCP Server

The MCP server runs in stdio mode and is designed to be used with MCP-compatible clients like Claude Desktop:

```bash
python3 mcp_server.py
```

### Testing the Server

Use the interactive manual tester to verify functionality:

```bash
python3 mcp_manual_tester.py
```

The tester provides an interactive menu with options to:
- Create individual folders and files
- Create complete project structures
- List directory contents
- Clean up test files

### Available MCP Tools

#### `create_folder`
Creates a new folder at the specified path.

**Parameters:**
- `folder_path` (string): Path of the folder to create (e.g., "my-project" or "project/sub-folder")

**Example:**
```json
{
  "name": "create_folder",
  "arguments": {
    "folder_path": "my-new-project"
  }
}
```

#### `create_file`
Creates an empty file at the specified path.

**Parameters:**
- `file_path` (string): Path of the file to create (e.g., "readme.txt" or "project/config.json")

**Example:**
```json
{
  "name": "create_file",
  "arguments": {
    "file_path": "project/README.md"
  }
}
```

#### `list_contents`
Lists the contents of a directory.

**Parameters:**
- `folder_path` (string, optional): Path of the folder to list (empty for Desktop)

**Example:**
```json
{
  "name": "list_contents",
  "arguments": {
    "folder_path": "my-project"
  }
}
```

## Configuration

### Base Directory

By default, all operations are performed relative to the user's Desktop (`~/Desktop`). This can be changed by modifying the `base_path` in the `VoiceFileControllerServer` class constructor in `mcp_server.py`.

### Security

The server implements path sanitization and validation to ensure:
- No directory traversal attacks (`../` sequences)
- Operations stay within the designated base directory
- Safe character handling in file/folder names

### Claude Desktop Integration

To use this MCP server with Claude Desktop:

1. Update your Claude Desktop configuration file with the contents from `claude_config.json`
2. Modify the paths to match your system:
   ```json
   {
     "mcpServers": {
       "mcp-file-controller": {
         "command": "python3",
         "args": ["mcp_server.py"],
         "cwd": "/path/to/your/mcp-producer",
         "env": {
           "PYTHONPATH": "/path/to/your/mcp-producer"
         }
       }
     }
   }
   ```

## Development

### Project Cleanup

This project has been cleaned up to contain only MCP-related functionality. All voice processing, audio handling, and OpenAI integration components have been removed to focus solely on the file management MCP server.

### Testing

The `mcp_manual_tester.py` script provides comprehensive testing capabilities:

- **Interactive Mode**: Menu-driven interface for testing all functions
- **Batch Operations**: Create multiple folders/files at once
- **Project Templates**: Generate complete project structures
- **Cleanup Tools**: Remove test files and folders

### Error Handling

The server implements proper MCP error handling with:
- JSON-RPC error codes
- Descriptive error messages
- Input validation
- Permission and file system error handling

## Requirements

- Python 3.7+
- `mcp` package (see requirements.txt)

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
