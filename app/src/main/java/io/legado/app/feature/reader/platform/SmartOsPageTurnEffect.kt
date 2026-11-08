package io.legado.app.feature.reader.platform

import android.os.Build
import io.legado.app.feature.reader.core.transition.ReaderWaterRipplePolicy
import io.legado.app.feature.reader.core.transition.ReaderWaterRippleSession
import timber.log.Timber

/** Vendor reflection stays in the Android adapter, never in rendering or settings UI. */
object SmartOsPageTurnEffect {
    private val command by lazy {
        runCatching {
            Class.forName("android.eink.EPDCDevice").getMethod("nativePostCommand", String::class.java)
        }.getOrNull()
    }

    val isSupported: Boolean by lazy {
        val isIReader = Build.MANUFACTURER.orEmpty().equals("iReader", true) || Build.BRAND.orEmpty().equals("iReader", true)
        isIReader && ReaderWaterRipplePolicy.isSupported(
            Build.MANUFACTURER.orEmpty(), Build.BRAND.orEmpty(), readVersion(), command != null,
        )
    }

    private fun readVersion(): String? {
        val reflected = runCatching {
            Class.forName("android.os.SystemProperties").getMethod("get", String::class.java)
                .invoke(null, "ro.build.versionCode") as? String
        }.getOrNull()
        if (!reflected.isNullOrBlank()) return reflected
        return runCatching {
            val process = ProcessBuilder("/system/bin/getprop", "ro.build.versionCode").start()
            try {
                process.inputStream.bufferedReader().use { it.readLine() }
            } finally {
                process.destroy()
            }
        }.getOrNull()
    }

    fun newSession(): ReaderWaterRippleSession = ReaderWaterRippleSession(
        supported = isSupported,
        sendCommand = { value -> checkNotNull(command).invoke(null, value); Unit },
        onFailure = { Timber.tag("SmartOsPageTurn").w(it, "Water ripple disabled for this reader session") },
    )
}
