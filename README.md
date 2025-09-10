source .venv/bin/activate

pytest -s -vv
pytest -s -vv -k 'some_test'
pytest -s -vv --hypothesis-profile debug

uv run stop-the-bus

./tail-latest-log.sh