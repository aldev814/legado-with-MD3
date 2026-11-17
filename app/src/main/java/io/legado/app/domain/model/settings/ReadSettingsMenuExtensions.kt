package io.legado.app.domain.model.settings

/** The nine-zone click configuration must retain at least one menu entry. */
internal fun ReadSettings.hasMenuClickArea(): Boolean =
    clickActionTL * clickActionTC * clickActionTR *
        clickActionML * clickActionMC * clickActionMR *
        clickActionBL * clickActionBC * clickActionBR == 0
