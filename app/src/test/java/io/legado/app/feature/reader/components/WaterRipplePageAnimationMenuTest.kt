package io.legado.app.feature.reader.components

import android.app.Application
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.unit.dp
import io.legado.app.R
import io.legado.app.constant.PageAnim
import io.legado.app.domain.model.settings.AppShellSettings
import io.legado.app.domain.model.settings.AppUiConfiguration
import io.legado.app.ui.book.read.ReadBookStyleConfig
import io.legado.app.ui.book.read.ReadBookIntent
import io.legado.app.ui.book.read.ConfigUpdate
import io.legado.app.ui.book.read.sheet.GlobalThemePage
import io.legado.app.ui.theme.AppTheme
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import org.robolectric.annotation.LooperMode
import splitties.init.injectAsAppCtx

@RunWith(RobolectricTestRunner::class)
@Config(application = Application::class, sdk = [35], qualifiers = "zh-rCN-w400dp-h1200dp")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@LooperMode(LooperMode.Mode.PAUSED)
class WaterRipplePageAnimationMenuTest {
    @get:Rule val compose = createComposeRule()

    private fun exercise(engine: String, selectSpeed: Boolean) {
        val app = RuntimeEnvironment.getApplication().also { it.injectAsAppCtx() }
        var expanded by mutableStateOf(true)
        val animations = mutableListOf<Int>()
        val speeds = mutableListOf<Int>()
        var dismisses = 0
        val style = ReadBookStyleConfig(
            waterRippleSupported = true, bookPageAnim = 9,
            effectivePageAnim = if (selectSpeed) 9 else PageAnim.noAnim,
            waterRippleSpeed = 1, pageAnimSpeed = 3,
        )
        compose.setContent {
            AppTheme(AppUiConfiguration(appShell = AppShellSettings(composeEngine = engine))) {
                Box(Modifier.size(200.dp)) {
                    WaterRipplePageAnimationMenu(
                        expanded = expanded, style = style, modifier = Modifier.matchParentSize(),
                        onAnimationChanged = { animations += it },
                        onSpeedChanged = { speeds += it },
                        onDismissRequest = { dismisses++; expanded = false },
                    )
                }
            }
        }
        compose.waitForIdle()
        val slow = app.getString(R.string.water_ripple_slow)
        if (selectSpeed) {
            val lists = compose.onAllNodes(hasScrollToIndexAction(), useUnmergedTree = true)
            if (lists.fetchSemanticsNodes().isNotEmpty()) lists.onLast().performScrollToNode(hasText(slow))
            else if (compose.onAllNodes(
                    hasText(slow) and hasAnyAncestor(hasScrollAction()), useUnmergedTree = true,
                ).fetchSemanticsNodes().isNotEmpty()) {
                compose.onNodeWithText(slow, useUnmergedTree = true).performScrollTo()
            }
            compose.onNodeWithText(slow, useUnmergedTree = true).assertIsDisplayed().performClick()
            compose.runOnIdle { assertEquals(listOf(2), speeds); assertEquals(emptyList<Int>(), animations) }
        } else {
            compose.onNodeWithText(slow, useUnmergedTree = true).assertDoesNotExist()
            compose.onNodeWithText(app.getString(R.string.btn_default_s), useUnmergedTree = true).performClick()
            compose.runOnIdle { assertEquals(listOf(-1), animations); assertEquals(emptyList<Int>(), speeds) }
        }
        compose.runOnIdle {
            assertTrue(dismisses >= 1)
            assertFalse(expanded)
            assertEquals(3, style.pageAnimSpeed)
        }
    }

    private fun globalSpeed(supported: Boolean, animation: Int, ripple: Boolean) {
        val app = RuntimeEnvironment.getApplication().also { it.injectAsAppCtx() }
        val intents = mutableListOf<ReadBookIntent>()
        compose.setContent {
            AppTheme(AppUiConfiguration()) {
                GlobalThemePage(
                    onToggleDayNight = {}, eyeProtectionEnabled = false,
                    onOpenBgTextConfig = {}, onOpenTypographyConfig = {}, onOpenPaddingConfig = {},
                    onShareLayoutChange = {}, onStyleSelect = {}, onIntent = { intents += it },
                    modifier = Modifier.fillMaxSize(),
                    styleConfig = ReadBookStyleConfig(
                        waterRippleSupported = supported, pageAnim = animation,
                        waterRippleSpeed = 1, pageAnimSpeed = 3,
                    ),
                )
            }
        }
        compose.onNode(hasClickAction() and hasContentDescription(app.getString(R.string.page_anim_speed)))
            .performScrollTo().performClick()
        val label = app.getString(if (ripple) R.string.water_ripple_slow else R.string.page_anim_speed_elegant)
        compose.onNodeWithText(label, useUnmergedTree = true).performClick()
        val expected = if (ripple) ConfigUpdate.WaterRippleSpeed(2) else ConfigUpdate.PageAnimSpeed(3)
        compose.runOnIdle { assertEquals(listOf(ReadBookIntent.UpdateConfig(expected)), intents) }
    }

    @Test fun globalRippleSpeedIsIndependent() = globalSpeed(true, 9, true)
    @Test fun globalOrdinarySpeedRetainsFourChoices() = globalSpeed(true, 1, false)
    @Test fun unsupportedStoredRippleUsesOrdinarySpeed() = globalSpeed(false, 9, false)
    @Test @Config(qualifiers = "zh-rCN-w1000dp-h700dp")
    fun expandedSpeedMenuScrolls() = exercise("material", true)

    @Test fun materialSpeed() = exercise("material", true)
    @Test fun materialDefault() = exercise("material", false)
    @Test fun miuixSpeed() = exercise("miuix", true)
    @Test fun miuixDefault() = exercise("miuix", false)
    @Test fun mochiSpeed() = exercise("mochi", true)
    @Test fun mochiDefault() = exercise("mochi", false)
    @Test fun couiSpeed() = exercise("coui", true)
    @Test fun couiDefault() = exercise("coui", false)
}
