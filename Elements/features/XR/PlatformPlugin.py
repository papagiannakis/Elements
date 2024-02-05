import abc
import platform

class PlatoformPlugin(object):
    "Can be used to create different implementation based on the platform"
    # Used to define in which platform this is running, e.g., Windows, Linux

    @abc.abstractmethod
    def __enter__(self):
        pass

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up platform resources."""

    @property
    @abc.abstractmethod
    def get_instance_Create_Extensions(self):
        pass

    @property
    @abc.abstractmethod
    def instance_extensions(self):
        pass

    @abc.abstractmethod
    def update_options(self, options) -> None:
        pass

class WindowsPlugin(PlatoformPlugin):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def instance_create_extension(self):
        return None

    @property
    def instance_extensions(self):
        # maybe for Linux additional libraries are needed here
        return []

    def update_options(self, options) -> None:
        pass

def createPlatformPlugin():
    "Other Platforms can be added here in the future"

    if platform.system() == "Windows":
        return WindowsPlugin()
    raise NotImplementedError