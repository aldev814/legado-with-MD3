package io.legado.app.ui.book.read.sheet

import androidx.compose.foundation.layout.Column
import androidx.compose.runtime.Composable
import androidx.compose.ui.res.stringResource
import io.legado.app.R
import io.legado.app.feature.reader.model.readerPageAnimationOptions
import io.legado.app.constant.PageAnim
import io.legado.app.feature.reader.components.WaterRippleSpeedSetting
import io.legado.app.ui.book.read.ReadBookStyleConfig
import io.legado.app.ui.book.read.ReadBookIntent
import io.legado.app.ui.book.read.ConfigUpdate
import io.legado.app.model.ReadBook
import io.legado.app.ui.widget.components.alert.AppAlertDialog
import io.legado.app.ui.widget.components.settingItem.TinyDropdownSettingItem

@Composable
fun PageAnimConfigSheet(
    onDismissRequest: () -> Unit,
    onAnimChanged: () -> Unit,
    styleConfig: ReadBookStyleConfig,
    onIntent: (ReadBookIntent) -> Unit,
) {
    // 每项自带 PageAnim 取值，不按「下标 - 1」推导：列表少一项就会整体错位一格
    // （最后一项写着「无动画」，落库的却是别的值）。
    val items = readerPageAnimationOptions(styleConfig.waterRippleSupported, includeDefault = true)

    // 调用方按 when(sheet) 条件组合本弹窗，所以这里 show 恒为 true；没有确定/取消按钮，
    // 普通动画选中后关闭；水波纹保留弹窗以便继续选择独立速度。
    AppAlertDialog(
        show = true,
        onDismissRequest = onDismissRequest,
        title = stringResource(R.string.page_anim),
        content = {
            Column {
                TinyDropdownSettingItem(
                    title = stringResource(R.string.page_anim),
                    selectedValue = if (!styleConfig.waterRippleSupported &&
                        styleConfig.bookPageAnim == PageAnim.waterRipplePageAnim
                    ) PageAnim.noAnim.toString() else styleConfig.bookPageAnim.toString(),
                    displayEntries = items.map { stringResource(it.label) }.toTypedArray(),
                    entryValues = items.map { it.value.toString() }.toTypedArray(),
                    onValueChange = {
                        ReadBook.book?.setPageAnim(it.toInt())
                        onAnimChanged()
                        if (it.toInt() != PageAnim.waterRipplePageAnim) onDismissRequest()
                    },
                )
                if (styleConfig.waterRippleSupported && styleConfig.effectivePageAnim == PageAnim.waterRipplePageAnim) {
                    WaterRippleSpeedSetting(styleConfig.waterRippleSpeed) {
                        onIntent(ReadBookIntent.UpdateConfig(ConfigUpdate.WaterRippleSpeed(it)))
                    }
                }
            }
        },
    )
}
