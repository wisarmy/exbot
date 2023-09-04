import logging

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
# 灰色
GREY = 30
# 深灰色
DARKGREY = 90


COLORS = {
    "WARNING": YELLOW,
    "INFO": GREEN,
    "DEBUG": BLUE,
    "CRITICAL": YELLOW,
    "ERROR": RED,
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        msg = logging.Formatter.format(self, record)

        if self.use_color:
            msg = self.colorize(msg, record)

        return msg

    def colorize(self, msg, record):
        levelname = record.levelname
        color = COLORS.get(levelname, WHITE)
        # 把前缀设置为灰色
        prefix = "\033[{}m{}".format(GREY, msg.split("\n", 1)[0])

        msg = msg.split("\n", 1)[1]
        colored_msg = "\033[{}m{}".format(30 + color, msg)

        return prefix + "\n" + colored_msg + "\033[0m"


colored_formatter = ColoredFormatter(
    "%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s\n%(message)s"
)

handler = logging.StreamHandler()
handler.setFormatter(colored_formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def setup_datalogger(log_file):
    datalogger = logging.getLogger("data_logger")
    datalogger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s, %(message)s")
    file_handler = logging.FileHandler(f"logs/{log_file}")
    file_handler.setFormatter(formatter)
    datalogger.addHandler(file_handler)

    return datalogger
