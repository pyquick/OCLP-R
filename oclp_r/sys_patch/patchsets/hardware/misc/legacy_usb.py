"""
legacy_usb.py: Legacy USB patch set for macOS 26+
"""

from ..base import BaseHardware, HardwareVariant

from ...base import PatchType

from .....constants import Constants

from .....datasets.os_data import os_data


class LegacyUSBHost(BaseHardware):

    def __init__(self, xnu_major, xnu_minor, os_build, global_constants: Constants) -> None:
        super().__init__(xnu_major, xnu_minor, os_build, global_constants)


    def name(self) -> str:
        """
        Display name for end users
        """
        return f"{self.hardware_variant()}: Legacy USB"

    def requires_kernel_debug_kit(self) -> bool:
        """
        Disable KDK requirement as we're only replacing existing kexts
        """
        return self._xnu_major >= os_data.tahoe.value
    def present(self) -> bool:
        return self._constants.allow_usb_patch


    def native_os(self) -> bool:
        return self._xnu_major < os_data.tahoe.value


    def hardware_variant(self) -> HardwareVariant:
        """
        Type of hardware variant
        """
        return HardwareVariant.MISCELLANEOUS


    def _legacy_usb_patches(self) -> dict:
        """
        Patches for Modern Audio
        Including:
        - IOUSBMassStorageDriver.kext (USB)
        - IOUSBDeviceFamily.kext (USB)
        - IOUSBFamily.kext (USB)
        - IOUSBHostFamily.kext (USB)
        """
        return {
            "Legacy USB": {
                PatchType.OVERWRITE_SYSTEM_VOLUME: {
                    "/System/Library/Extensions": {
                        "AppleUSBACM.kext": "15.5",  
                        "AppleUSBAudio.kext": "15.5",  
                        "AppleUSBCDC.kext": "15.5",  
                        "AppleUSBCommon.kext": "15.5",  
                        "AppleUSBDeviceMux.kext": "15.5",  
                        "AppleUSBDeviceNCM.kext": "15.5",  
                        "AppleUSBDisplays.kext": "15.5",  
                        "AppleUSBDMM.kext": "15.5",  
                        "AppleUSBECM.kext": "15.5",  
                        "AppleUSBEEM.kext": "15.5",  
                        "AppleUSBEthernet.kext": "15.5",  
                        "AppleUSBEthernetHost.kext": "15.5",  
                        "AppleUSBHostS5L8930X.kext": "15.5",  
                        "AppleUSBHostS5L8960X.kext": "15.5",  
                        "AppleUSBHostT7000.kext": "15.5",  
                        "AppleUSBHostT8002.kext": "15.5",  
                        "AppleUSBHostT8011.kext": "15.5",  
                        "AppleUSBHostT8020.kext": "15.5",  
                        "AppleUSBHSIC.kext": "15.5",  
                        "AppleUSBiBridge.kext": "15.5",  
                        "AppleUSBLightningAdapter.kext": "15.5",  
                        "AppleUSBMike.kext": "15.5",  
                        "AppleUSBNCM.kext": "15.5",  
                        "AppleUSBNetworking.kext": "15.5",  
                        "AppleUSBRealtek8153Patcher.kext": "15.5",  
                        "AppleUSBSerial.kext": "15.5",  
                        "AppleUSBWCM.kext": "15.5",  
                        "IOUSBDeviceFamily.kext": "15.5",  
                        "IOUSBFamily.kext": "15.5",  
                        "IOUSBHostFamily.kext": "15.5",  
                        "IOUSBMassStorageDriver.kext": "15.5",
                    },
                },
            },
        }


    def patches(self) -> dict:
        """
        Patches for modern audio
        """
        if self.native_os() is True:
            return {}

        return self._legacy_usb_patches()