#!/bin/bash

echo "Entrypoint: VectorDB Container is running!!!"

if [ "${DEV}" = 1 ]; then
  pipenv shell
else
  pipenv run python cli.py --download --load
fi
