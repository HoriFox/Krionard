import sys
import argparse
from server import create_app

parser = argparse.ArgumentParser(description='Marusya skill server executor')
parser.add_argument('-c', '--config', type=str,
                    default='/etc/assol/skill.config.json',
                    help='Config file for Marusya skill server')
parser.add_argument('-v', '--vocabulary', type=str,
                    default='/etc/assol/skill.vocabulary.json',
                    help='Vocabulary file for Marusya skill server')
args = parser.parse_args()

app = create_app(args.config, args.vocabulary)

if __name__ == "__main__":
    app.run(port=8080) #debug = True

