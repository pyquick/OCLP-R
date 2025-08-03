"""
whatevergreen.py: GPU(RX580+) patch set for macOS 26
"""

from ..base import BaseHardware, HardwareVariant

from ...base import PatchType

from .....constants import Constants

from .....datasets.os_data import os_data


class WEG(BaseHardware):

    def __init__(self, xnu_major, xnu_minor, os_build, global_constants: Constants) -> None:
        super().__init__(xnu_major, xnu_minor, os_build, global_constants)


    def name(self) -> str:
        """
        Display name for end users
        """
        return f"{self.hardware_variant()}: WhateverGreen"


    def present(self) -> bool:
       
        return True


    def check_if_patch(self) -> bool:
        import subprocess
        kexts=subprocess.run("kextstat | grep -v com.apple",shell=True,capture_output=True,text=True).stdout
        if "as.vit9696.WhateverGreen" in kexts:
            return True
        return False
    

    def native_os(self) -> bool:
        if self._xnu_major < os_data.tahoe.value or self.check_if_patch():
            return True

        return False


    def hardware_variant(self) -> HardwareVariant:
        """
        Type of hardware variant
        """
        return HardwareVariant.MISCELLANEOUS


    def _weg_patches(self) -> dict:
        """
        Patches for Whatevergreen
        """
        return {
            "WhateverGreen": {
                PatchType.OVERWRITE_SYSTEM_VOLUME: {
                    "/System/Library/Extensions": {
                        "WhateverGreen.kext":      "WhateverGreen",
                        "Lilu.kext":               "WhateverGreen",
                    },
                },
            },
        }


    def patches(self) -> dict:
        """
        Patches for modern audio
        """
        if self.native_os() is True :
            return {}
        if self.check_if_patch() is True:
            return {}
        return self._weg_patches()