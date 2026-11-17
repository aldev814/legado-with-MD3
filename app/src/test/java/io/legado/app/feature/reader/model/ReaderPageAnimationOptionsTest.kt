package io.legado.app.feature.reader.model

import io.legado.app.constant.PageAnim
import org.junit.Assert.*
import org.junit.Test

class ReaderPageAnimationOptionsTest {
    @Test fun `compatibility filters only water ripple and preserves persisted values`() {
        val ordinary = readerPageAnimationOptions(false)
        val supported = readerPageAnimationOptions(true)
        assertEquals(listOf(0, 1, 2, 6, 7, 8, 3, 4, 5), ordinary.map { it.value })
        assertEquals(ordinary, supported.filter { it.value != PageAnim.waterRipplePageAnim })
        assertEquals(1, supported.count { it.value == 9 })
        assertEquals(-1, readerPageAnimationOptions(true, true).first().value)
        assertEquals(ordinary.size + 1, readerPageAnimationOptions(false, true).size)
    }
    @Test fun `unsupported display fallback preserves defaults and ordinary animation values`() {
        for (value in -1..8) assertEquals(value, readerVisiblePageAnimation(value, false))
        assertEquals(PageAnim.noAnim, readerVisiblePageAnimation(9, false))
        assertEquals(9, readerVisiblePageAnimation(9, true))
    }
}
