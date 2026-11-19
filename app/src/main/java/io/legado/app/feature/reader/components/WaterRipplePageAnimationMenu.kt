package io.legado.app.feature.reader.components

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import io.legado.app.R
import io.legado.app.constant.PageAnim
import io.legado.app.feature.reader.model.readerPageAnimationOptions
import io.legado.app.ui.book.read.ReadBookStyleConfig
import io.legado.app.ui.widget.components.menu.AppAction
import io.legado.app.ui.widget.components.menu.AppActionGroup
import io.legado.app.ui.widget.components.menu.AppActionMenu
import kotlinx.collections.immutable.toImmutableList

private const val AnimationPrefix = "ireader_animation:"
private const val SpeedPrefix = "ireader_speed:"

/** Supported-device decoration of the host's controlled menu; all effects stay with callbacks. */
@Composable
fun WaterRipplePageAnimationMenu(
    expanded: Boolean,
    style: ReadBookStyleConfig,
    onAnimationChanged: (Int) -> Unit,
    onSpeedChanged: (Int) -> Unit,
    onDismissRequest: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val options = readerPageAnimationOptions(supported = true, includeDefault = true)
    val groups = buildList {
        add(AppActionGroup(
            id = "ireader_animations",
            actions = options.map { option -> AppAction(
                id = "$AnimationPrefix${option.value}", label = stringResource(option.label),
                selected = style.bookPageAnim == option.value,
            ) }.toImmutableList(),
        ))
        if (style.effectivePageAnim == PageAnim.waterRipplePageAnim) {
            add(AppActionGroup(
                id = "ireader_speeds",
                actions = listOf(R.string.water_ripple_fast, R.string.water_ripple_standard, R.string.water_ripple_slow)
                    .mapIndexed { speed, label -> AppAction(
                        id = "$SpeedPrefix$speed", label = stringResource(label),
                        selected = style.waterRippleSpeed == speed,
                    ) }.toImmutableList(),
            ))
        }
    }.toImmutableList()
    AppActionMenu(
        groups = groups,
        onAction = { id ->
            when {
                id.startsWith(AnimationPrefix) -> id.removePrefix(AnimationPrefix).toIntOrNull()
                    ?.takeIf { value -> options.any { it.value == value } }?.let(onAnimationChanged)
                id.startsWith(SpeedPrefix) -> id.removePrefix(SpeedPrefix).toIntOrNull()
                    ?.takeIf { it in 0..2 }?.let(onSpeedChanged)
            }
        },
        modifier = modifier, embeddedExpanded = expanded,
        onDismissRequest = onDismissRequest, trigger = {},
    )
}
