import {useState} from 'react';
import {useTranslation} from 'react-i18next';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import {
    arvoGetImpersonoitavaByName$,
    arvoGetKoulutustoimijaByName$,
    arvoImpersonoi$,
    ArvoKoulutustoimija,
    arvoVaihdaOrganisaatio$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import MenuItem from '@mui/material/MenuItem';
import navistyles from '@cscfi/shared/components/Navigaatio/Navigaatio.module.css';
import ImpersonateSearch from './ImpersonateSearch';

function ImpersonateStart() {
    const {t} = useTranslation(['impersonointi-avustus']);
    const [oid, setOid] = useState<string | null>(null);

    const refresh = () => {
        window.location.replace(`${window.location.origin}/virkailija-ui/`);
    };

    return (
        <>
            <ConfirmationDialog
                confirmBtnDisabled={!oid}
                confirmBtnText={t('vaihda', {
                    ns: 'impersonointi-avustus',
                })}
                title={t('vaihda-title', {ns: 'impersonointi-avustus'})}
                confirm={() => {
                    arvoImpersonoi$(oid!).subscribe({
                        next: () => {
                            setOid(null);
                            refresh();
                        },
                    });
                }}
                content={
                    <ImpersonateSearch
                        translationNs="impersonointi-avustus"
                        setOid={setOid}
                        fetchFn={arvoGetImpersonoitavaByName$}
                    />
                }
            >
                <MenuItem className={navistyles.impersonation}>
                    {t('menu-button', {ns: 'impersonointi-avustus'})}
                </MenuItem>
            </ConfirmationDialog>

            <ConfirmationDialog
                confirmBtnDisabled={!oid}
                confirmBtnText={t('vaihda', {
                    ns: 'impersonointi-organisaatio',
                })}
                title={t('vaihda-title', {ns: 'impersonointi-organisaatio'})}
                confirm={() => {
                    arvoVaihdaOrganisaatio$(oid!).subscribe({
                        next: () => {
                            setOid(null);
                            refresh();
                        },
                    });
                }}
                content={
                    <ImpersonateSearch
                        translationNs="impersonointi-organisaatio"
                        setOid={setOid}
                        fetchFn={arvoGetKoulutustoimijaByName$}
                        filterFn={(obj: ArvoKoulutustoimija) =>
                            obj.tyypit.includes('organisaatiotyyppi_09')
                        }
                    />
                }
            >
                <MenuItem className={navistyles.impersonation}>
                    {t('menu-button', {ns: 'impersonointi-organisaatio'})}
                </MenuItem>
            </ConfirmationDialog>
        </>
    );
}

export default ImpersonateStart;
