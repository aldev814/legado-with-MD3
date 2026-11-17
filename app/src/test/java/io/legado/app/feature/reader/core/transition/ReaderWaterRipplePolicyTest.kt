package io.legado.app.feature.reader.core.transition

import io.legado.app.feature.reader.core.model.ReaderPage
import io.legado.app.feature.reader.core.model.ReaderPageId
import org.junit.Assert.*
import org.junit.Test

class ReaderWaterRipplePolicyTest {
    private fun page(chapter: Int = 0, index: Int = 0, placeholder: Boolean = false) = ReaderPage(
        id = ReaderPageId(chapter, index), chapterTitle = "Chapter", text = "Page",
        widthPx = 600, heightPx = 800, contentTopPx = 0f, contentBottomPx = 800f,
        elements = emptyList(), revision = 0L, isPlaceholder = placeholder,
    )

    @Test fun `water ripple has a distinct persisted value and no software transforms`() {
        assertEquals(ReaderTransitionMode.WATER_RIPPLE, ReaderTransitionMode.fromPageAnim(9))
        val turn = ReaderPageTransition(ReaderTurnDirection.NEXT, -200f, 400f, true)
        val transforms = turn.transforms(ReaderTransitionMode.WATER_RIPPLE)
        assertEquals(0f, transforms.current.translationX, 0f)
        assertNull(transforms.next)
        assertNull(transforms.previous)
    }

    @Test fun `capability requires brand version and command`() {
        assertTrue(ReaderWaterRipplePolicy.isSupported("IREADER", "other", "4.2", true))
        assertTrue(ReaderWaterRipplePolicy.isSupported("other", "iReader", "5.0", true))
        for (version in listOf(null, "", "unknown", "3.9")) {
            assertFalse(ReaderWaterRipplePolicy.isSupported("iReader", "iReader", version, true))
        }
        assertFalse(ReaderWaterRipplePolicy.isSupported("other", "other", "4.0", true))
        assertFalse(ReaderWaterRipplePolicy.isSupported("iReader", "iReader", "4.0", false))
    }

    @Test fun `direction and speed match reference commands for every rotation`() {
        val next = listOf(1, 4, 2, 3)
        val previous = listOf(2, 3, 1, 4)
        for (rotation in 0..3) for (speed in ReaderWaterRippleSpeed.entries) {
            assertEquals(next[rotation] or speed.commandFlag,
                ReaderWaterRipplePolicy.commandCode(ReaderTurnDirection.NEXT, rotation, speed))
            assertEquals(previous[rotation] or speed.commandFlag,
                ReaderWaterRipplePolicy.commandCode(ReaderTurnDirection.PREVIOUS, rotation, speed))
        }
        assertEquals(ReaderWaterRippleSpeed.STANDARD, ReaderWaterRippleSpeed.fromValue(-1))
        assertEquals(ReaderWaterRippleSpeed.STANDARD, ReaderWaterRippleSpeed.fromValue(3))
    }

    @Test fun `only a committed readable change sends a command`() {
        val commands = mutableListOf<String>()
        val session = ReaderWaterRippleSession(true, commands::add) { throw AssertionError(it) }
        val origin = page()
        val target = page(index = 1)
        for ((from, to) in listOf(
            origin to null, null to target, origin to origin,
            origin to origin.copy(revision = 1L), origin to target.copy(isPlaceholder = true),
            origin.copy(isPlaceholder = true) to target,
        )) {
            session.onPageChanged(ReaderTurnDirection.NEXT, 0, ReaderWaterRippleSpeed.STANDARD, from, to)
        }
        assertTrue(commands.isEmpty())
        session.onPageChanged(ReaderTurnDirection.NEXT, 0, ReaderWaterRippleSpeed.STANDARD, origin, target)
        assertEquals(listOf("next-effect-type 65"), commands)
    }

    @Test fun `chapter boundary direction does not depend on page number reset`() {
        val commands = mutableListOf<String>()
        val session = ReaderWaterRippleSession(true, commands::add) { throw AssertionError(it) }
        val last = page(chapter = 0, index = 99)
        val first = page(chapter = 1, index = 0)
        session.onPageChanged(ReaderTurnDirection.NEXT, 0, ReaderWaterRippleSpeed.FAST, last, first)
        session.onPageChanged(ReaderTurnDirection.PREVIOUS, 0, ReaderWaterRippleSpeed.FAST, first, last)
        assertEquals(listOf("next-effect-type 1", "next-effect-type 2"), commands)
    }

    @Test fun `unsupported and failed sessions never retry hardware`() {
        var calls = 0
        var failures = 0
        val unsupported = ReaderWaterRippleSession(false, { calls++ }) { failures++ }
        unsupported.onPageChanged(ReaderTurnDirection.NEXT, 0, ReaderWaterRippleSpeed.FAST, page(), page(index = 1))
        val failed = ReaderWaterRippleSession(true, { calls++; error("unavailable") }) { failures++ }
        repeat(3) { failed.onPageChanged(ReaderTurnDirection.NEXT, 0, ReaderWaterRippleSpeed.FAST, page(), page(index = 1)) }
        assertEquals(1, calls)
        assertEquals(1, failures)
    }
}
