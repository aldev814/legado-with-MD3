package io.legado.app.feature.reader.model

import androidx.annotation.StringRes
import androidx.compose.runtime.Stable
import io.legado.app.R
import io.legado.app.constant.PageAnim
import kotlinx.collections.immutable.ImmutableList
import kotlinx.collections.immutable.toImmutableList

@Stable
data class ReaderPageAnimationOption(@param:StringRes val label: Int, val value: Int)

fun readerPageAnimationOptions(
    supported: Boolean,
    includeDefault: Boolean = false,
): ImmutableList<ReaderPageAnimationOption> =
    buildList {
        if (includeDefault) add(ReaderPageAnimationOption(R.string.btn_default_s, -1))
        add(ReaderPageAnimationOption(R.string.page_anim_cover, PageAnim.coverPageAnim))
        add(ReaderPageAnimationOption(R.string.page_anim_slide, PageAnim.slidePageAnim))
        add(ReaderPageAnimationOption(R.string.page_anim_simulation, PageAnim.simulationPageAnim))
        add(ReaderPageAnimationOption(R.string.page_anim_ios_curl, PageAnim.iosCurlPageAnim))
        add(ReaderPageAnimationOption(R.string.page_anim_google_curl, PageAnim.googleCurlPageAnim))
        add(ReaderPageAnimationOption(R.string.page_anim_parallax, PageAnim.parallaxPageAnim))
        add(ReaderPageAnimationOption(R.string.page_anim_scroll, PageAnim.scrollPageAnim))
        add(ReaderPageAnimationOption(R.string.page_anim_fade, PageAnim.fadePageAnim))
        if (supported) add(ReaderPageAnimationOption(R.string.page_anim_water_ripple, PageAnim.waterRipplePageAnim))
        add(ReaderPageAnimationOption(R.string.page_anim_none, PageAnim.noAnim))
    }.toImmutableList()
