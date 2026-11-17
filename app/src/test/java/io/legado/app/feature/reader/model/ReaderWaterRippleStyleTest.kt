package io.legado.app.feature.reader.model

import io.legado.app.help.config.ReadBookConfig
import io.legado.app.help.config.ReadStyleResolver.ReadStyleMode
import io.legado.app.ui.book.read.ReadBookStyleConfig
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class ReaderWaterRippleStyleTest {
    @Test fun unsupportedDeviceRetainsStoredModeAndUnrelatedStyleFields() {
        val base = ReadBookStyleConfig(styleName = "kept", textSize = 31, pageAnimSpeed = 3)
        val config = ReadBookConfig.Config(pageAnim = 9, waterRippleSpeed = 2)
        val actual = base.withWaterRipple(config, null, 0, ReadStyleMode.Day, false)
        assertEquals(base.copy(pageAnim = 9, waterRippleSpeed = 2), actual)
        assertFalse(actual.waterRippleSupported)
        assertEquals(0, actual.effectivePageAnim)
    }

    @Test fun dayNightAndEInkUseTheirOwnStoredAnimation() {
        val config = ReadBookConfig.Config(pageAnim = 2, pageAnimEInk = 9, waterRippleSpeed = 0)
        for (mode in ReadStyleMode.entries) {
            val actual = ReadBookStyleConfig().withWaterRipple(config, 9, 9, mode, true)
            assertEquals(if (mode == ReadStyleMode.EInk) 9 else 2, actual.pageAnim)
            assertEquals(0, actual.waterRippleSpeed)
            assertEquals(9, actual.bookPageAnim)
            assertEquals(9, actual.effectivePageAnim)
        }
    }

    @Test fun defaultBookOverrideAndInvalidSpeedAreNormalizedIndependently() {
        val config = ReadBookConfig.Config(waterRippleSpeed = 99, pageAnimSpeed = 3)
        for (override in listOf(null, -1, -7, 0, 9)) {
            val base = ReadBookStyleConfig(pageAnimSpeed = 3)
            val actual = base.withWaterRipple(config, override, 2, ReadStyleMode.Day, true)
            assertEquals(override?.takeIf { it >= 0 } ?: -1, actual.bookPageAnim)
            assertEquals(1, actual.waterRippleSpeed)
            assertEquals(3, actual.pageAnimSpeed)
        }
    }
}
