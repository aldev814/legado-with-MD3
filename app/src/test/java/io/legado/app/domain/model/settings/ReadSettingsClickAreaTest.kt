package io.legado.app.domain.model.settings

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ReadSettingsClickAreaTest {
    @Test fun defaultGridRetainsAMenuEntry() {
        assertTrue(ReadSettings().hasMenuClickArea())
    }

    @Test fun gridWithoutAMenuIsRecognized() {
        assertFalse(ReadSettings(clickActionMC = 1).hasMenuClickArea())
    }

    @Test fun everyZoneCanProvideTheMenuEntry() {
        val withoutMenu = ReadSettings(clickActionMC = 1)
        val variants = listOf(
            withoutMenu.copy(clickActionTL = 0), withoutMenu.copy(clickActionTC = 0),
            withoutMenu.copy(clickActionTR = 0), withoutMenu.copy(clickActionML = 0),
            withoutMenu.copy(clickActionMC = 0), withoutMenu.copy(clickActionMR = 0),
            withoutMenu.copy(clickActionBL = 0), withoutMenu.copy(clickActionBC = 0),
            withoutMenu.copy(clickActionBR = 0),
        )
        variants.forEach { assertTrue(it.hasMenuClickArea()) }
    }
}
