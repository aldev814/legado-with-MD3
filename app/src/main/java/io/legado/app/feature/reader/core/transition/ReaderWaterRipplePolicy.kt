package io.legado.app.feature.reader.core.transition

import io.legado.app.feature.reader.core.model.ReaderPage

/** Stable persisted values, independent of the ordinary animation duration. */
enum class ReaderWaterRippleSpeed(val value: Int, val commandFlag: Int) {
    FAST(0, 0), STANDARD(1, 64), SLOW(2, 128);

    companion object {
        fun fromValue(value: Int): ReaderWaterRippleSpeed = entries.firstOrNull { it.value == value } ?: STANDARD
    }
}

object ReaderWaterRipplePolicy {
    fun isSupported(manufacturer: String, brand: String, version: String?, hasCommand: Boolean): Boolean =
        (manufacturer.equals("iReader", true) || brand.equals("iReader", true)) &&
            (version?.substringBefore('.')?.toIntOrNull() ?: 0) >= 4 && hasCommand

    /** Rotation uses Android display rotation values 0..3, without Android dependencies. */
    fun commandCode(direction: ReaderTurnDirection, rotation: Int, speed: ReaderWaterRippleSpeed): Int {
        val forward = direction == ReaderTurnDirection.NEXT
        val code = when (rotation) {
            1 -> if (forward) 4 else 3
            2 -> if (forward) 2 else 1
            3 -> if (forward) 3 else 4
            else -> if (forward) 1 else 2
        }
        return code or speed.commandFlag
    }
}

/** One session owns failure suppression; callers invoke only for an actual, readable page change. */
class ReaderWaterRippleSession(
    private val supported: Boolean,
    private val sendCommand: (String) -> Unit,
    private val onFailure: (Throwable) -> Unit,
) {
    private var failed = false

    fun onPageChanged(
        direction: ReaderTurnDirection,
        rotation: Int,
        speed: ReaderWaterRippleSpeed,
        origin: ReaderPage?,
        destination: ReaderPage?,
    ) {
        if (!supported || failed || origin == null || destination == null ||
            origin.id == destination.id || origin.isPlaceholder || destination.isPlaceholder
        ) return
        try {
            sendCommand("next-effect-type ${ReaderWaterRipplePolicy.commandCode(direction, rotation, speed)}")
        } catch (error: Exception) {
            failed = true
            onFailure(error)
        }
    }
}
