package io.legado.app.ui.book.read

import java.io.File
import kotlin.reflect.full.primaryConstructor
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ReaderWaterRippleOwnershipTest {
    @Test fun sessionStaysWithTheReaderSessionOwner() {
        val fields = ReadBookUiState::class.primaryConstructor!!.parameters.map { it.name }
        assertFalse("Hardware session must not enter durable UI state", "waterRippleSession" in fields)
        val host = source("ReadBookViewModel.kt")
        assertFalse(host.contains("ReaderWaterRippleSession"))
        assertFalse(host.contains("waterRippleSession"))
        assertTrue(source("ReaderRenderUiState.kt").contains("val waterRippleSession by lazy"))
    }

    private fun source(name: String): String {
        var directory: File? = File("").absoluteFile
        while (directory != null) {
            val file = File(directory, "app/src/main/java/io/legado/app/ui/book/read/$name")
            if (file.isFile) return file.readText()
            directory = directory.parentFile
        }
        error("Reader owner source not found: $name")
    }
}
