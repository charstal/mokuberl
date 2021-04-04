FROM python:3.8.9-slim


COPY . /rl-server
WORKDIR /rl-server
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -f https://download.pytorch.org/whl/torch_stable.html
ENTRYPOINT [ "python3", "server.py" ]