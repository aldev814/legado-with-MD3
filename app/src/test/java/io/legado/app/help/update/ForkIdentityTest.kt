package io.legado.app.help.update

import io.legado.app.BuildConfig
import io.legado.app.utils.FirebaseManager
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class ForkIdentityTest {
    @Test fun independentPackageDoesNotReuseUpstreamFirebase() {
        assertEquals("io.legato.kazusa.ireader", BuildConfig.APPLICATION_ID.removeSuffix(".debug"))
        assertFalse(BuildConfig.FIREBASE_SUPPORTED)
        assertFalse(FirebaseManager.isSupported)
        assertFalse(FirebaseManager.isEnabled)
    }
}
