import threading
import time
from interaction_recognition import interaction_recognition


class StatementManager:
    def __init__(self, batch_size=20, timeout=5.0):
        """
        :param batch_size: 每批处理条数
        :param timeout: 超时时间(秒)
        """
        self.saved_statements = []
        self.lock = threading.RLock()
        self.batch_size = batch_size
        self.timeout = timeout
        self.last_process_time = time.time()
        self.timer = None
        self._start_timer()

    def _start_timer(self):
        """启动/重置定时器"""
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(
            self.timeout,
            self._timeout_handler
        )
        self.timer.start()

    def _timeout_handler(self):
        """超时处理回调"""
        with self.lock:
            if self.saved_statements:
                self._process_statements(force=True)

    def add_statements(self, new_statements):
        """添加新语句"""
        with self.lock:
            self.saved_statements.append(new_statements)
            self.last_process_time = time.time()

            # 达到批量大小时立即处理
            if len(self.saved_statements) >= self.batch_size:
                self._process_statements()
            else:
                self._start_timer()  # 重置定时器

    def _process_statements(self, force=False):
        """处理语句
        :param force: 是否强制处理(不满batch_size也处理)
        """
        with self.lock:
            if not self.saved_statements:
                return

            # 计算需要处理的条数
            process_count = min(
                len(self.saved_statements),
                self.batch_size if not force else len(self.saved_statements)
            )

            if process_count <= 0:
                return

            # 取出要处理的语句
            to_process = self.saved_statements[:process_count]
            # 删除已处理的语句
            self.saved_statements = self.saved_statements[process_count:]

            # 重置最后处理时间
            self.last_process_time = time.time()
            self._start_timer()  # 重置定时器

        # 在锁外调用处理函数
        another_function(to_process)

    def get_statement_count(self):
        """获取当前语句数量"""
        with self.lock:
            return len(self.saved_statements)

    def shutdown(self):
        """关闭时处理剩余语句"""
        with self.lock:
            if self.timer:
                self.timer.cancel()
            if self.saved_statements:
                self._process_statements(force=True)


def another_function(statements):
    """处理语句的函数"""
    if not statements:
        return

    # 生成带编号的字符串
    formatted_text = "\n".join(
        f"{i + 1}、{stmt}。\n"
        for i, stmt in enumerate(statements))
    interaction_recognition(formatted_text, statements)

    # 示例处理: 写入文件
    # with open("processed_statements.txt", "a", encoding="utf-8") as f:
    #     for stmt in statements:
    #         f.write(f"{stmt}\n")


# 全局实例
statement_manager = StatementManager(batch_size=20, timeout=10.0)
