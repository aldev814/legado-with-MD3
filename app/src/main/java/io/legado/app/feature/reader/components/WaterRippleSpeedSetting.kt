package io.legado.app.feature.reader.components

import androidx.compose.runtime.Composable
import androidx.compose.ui.res.stringResource
import io.legado.app.R
import io.legado.app.ui.widget.components.settingItem.TinyDropdownSettingItem

@Composable
fun WaterRippleSpeedSetting(speed: Int, onSpeedChange: (Int) -> Unit) {
    TinyDropdownSettingItem(
        title = stringResource(R.string.water_ripple_speed),
        selectedValue = speed.toString(),
        displayEntries = arrayOf(
            stringResource(R.string.water_ripple_fast),
            stringResource(R.string.water_ripple_standard),
            stringResource(R.string.water_ripple_slow),
        ),
        entryValues = arrayOf("0", "1", "2"),
        onValueChange = { onSpeedChange(it.toInt()) },
    )
}
