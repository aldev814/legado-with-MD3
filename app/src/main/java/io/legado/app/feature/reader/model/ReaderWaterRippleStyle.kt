package io.legado.app.feature.reader.model

import io.legado.app.feature.reader.platform.SmartOsPageTurnEffect
import io.legado.app.help.config.ReadBookConfig
import io.legado.app.help.config.ReadStyleResolver
import io.legado.app.ui.book.read.ReadBookStyleConfig

/** Decorate the existing reader snapshot without changing unrelated style fields. */
internal fun ReadBookStyleConfig.withWaterRipple(
    config: ReadBookConfig.Config,
    bookPageAnim: Int?,
    effectivePageAnim: Int,
    mode: ReadStyleResolver.ReadStyleMode = ReadStyleResolver.currentMode(),
    supported: Boolean = SmartOsPageTurnEffect.isSupported,
): ReadBookStyleConfig = copy(
    pageAnim = if (mode == ReadStyleResolver.ReadStyleMode.EInk) config.getPageAnimEInk() else config.getPageAnim(),
    waterRippleSpeed = config.getWaterRippleSpeed(),
    waterRippleSupported = supported,
    bookPageAnim = bookPageAnim?.takeIf { it >= 0 } ?: -1,
    effectivePageAnim = effectivePageAnim,
)
