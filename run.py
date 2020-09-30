import sys
from server import create_app

config = sys.argv[1] if len(sys.argv) > 1 else None
vocabulary = sys.argv[2] if len(sys.argv) > 2 else None

app = create_app(config, vocabulary)

if __name__ == "__main__":
    app.run(port=8080, debug=True)

