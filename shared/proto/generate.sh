#!/bin/bash
# Generate Python code from proto files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTO_DIR="$SCRIPT_DIR/../shared/proto"
OUTPUT_DIR="$SCRIPT_DIR/../shared/proto"

python3 -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$PROTO_DIR/service.proto"

echo "Generated files:"
ls -la "$OUTPUT_DIR"/*.py 2>/dev/null || echo "No Python files generated"
