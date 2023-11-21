import {useTranslation} from 'react-i18next';
import MenuItem from '@mui/material/MenuItem';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import {
    ArvoRooli,
    Oppilaitos,
    arvoVaihdaRooli$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import Button from '@mui/material/Button';
import navistyles from '@cscfi/shared/components/Navigaatio/Navigaatio.module.css';
import styles from './Impersontate.module.css';

interface ImpersonateRooliProps {
    aktiivinen: ArvoRooli;
    roolit: ArvoRooli[];
}

function ImpersonateRooli({roolit, aktiivinen}: ImpersonateRooliProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['impersonointi-rooli']);

    const rooliKoulutustoimija = `koulutustoimija_${lang}` as keyof ArvoRooli;
    const rooliOppilaitos = `oppilaitos_${lang}` as keyof Oppilaitos;

    const refresh = () => {
        window.location.replace(`${window.location.origin}/virkailija-ui/`);
    };

    return (
        <ConfirmationDialog
            confirmBtnText={t('peruuta')}
            title={t('vaihda-title')}
            content={
                <div className={styles.list}>
                    <ul>
                        {roolit.map((rooli) => (
                            <li key={rooli.rooli_organisaatio_id}>
                                <span className={styles.roletext}>
                                    <span className={styles['roletext-org']}>
                                        {rooli[rooliKoulutustoimija] as string}
                                    </span>
                                    {`: ${t(rooli.kayttooikeus.toLowerCase(), {
                                        ns: 'login',
                                    })}`}
                                    {rooli?.oppilaitokset &&
                                        rooli?.oppilaitokset.length > 0 &&
                                        ` (${rooli.oppilaitokset
                                            .map((opp) => opp[rooliOppilaitos])
                                            .join(', ')})`}
                                </span>
                                {rooli.rooli_organisaatio_id !==
                                    aktiivinen.rooli_organisaatio_id && (
                                    <Button
                                        className="verysmall"
                                        onClick={() =>
                                            arvoVaihdaRooli$(
                                                rooli.rooli_organisaatio_id!,
                                            ).subscribe({
                                                next: () => {
                                                    refresh();
                                                },
                                            })
                                        }
                                    >
                                        {t('vaihda')}
                                    </Button>
                                )}
                            </li>
                        ))}
                    </ul>
                </div>
            }
        >
            <MenuItem className={navistyles.impersonation}>{t('menu-button')}</MenuItem>
        </ConfirmationDialog>
    );
}

export default ImpersonateRooli;
