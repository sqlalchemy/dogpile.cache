import threading

import dogpile


class AsyncRunnerTest:
    def test_async_release(self):
        self.called = False

        def runner(mutex):
            self.called = True
            mutex.release()

        mutex = threading.Lock()
        create = lambda: ("value", 1)  # noqa
        get = lambda: ("value", 1)  # noqa
        expiretime = 1

        assert not self.called

        with dogpile.Lock(mutex, create, get, expiretime, runner) as _:
            assert self.called

        assert self.called
