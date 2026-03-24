import {useTranslation} from 'react-i18next';
import {useState} from 'react';
import {Observable} from 'rxjs';
import {AvailableKyselykertas} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {useLocation, useNavigate} from 'react-router-dom';
import {downloadCsv} from '@cscfi/shared/utils/helpers';
import {parseISO} from 'date-fns';
import DropDownField, {
    DropDownItem,
} from '@cscfi/shared/components/DropDownField/DropDownField';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import LaunchIcon from '@mui/icons-material/Launch';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import styles from '../../pages/Raportointi/raportit.module.css';
import GuardedComponentWrapper from '../GuardedComponentWrapper/GuardedComponentWrapper';

export enum ValitsinTyyppi {
    raportti = 'display_report',
    arviointutulos = 'show_result',
    yhteenveto = 'show_summary',
}

interface KyselykertaValitsinProps {
    availableKyselykertas?: AvailableKyselykertas[];
    kyselykertaStart?: string;
    tyyppi?: ValitsinTyyppi;
    sideEffects?: Array<() => void>;
    csvObservable?: Observable<string>;
    csvName?: string;
}

function KyselykertaValitsin({
    availableKyselykertas = [],
    kyselykertaStart,
    tyyppi = ValitsinTyyppi.raportti,
    sideEffects = [],
    csvObservable,
    csvName = 'vastaukset',
}: KyselykertaValitsinProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['raportointi']);
    const location = useLocation();
    const navigate = useNavigate();

    // Käyttäjän oma valinta; starttia ei kopioida stateen
    const [selectedKyselykerta, setSelectedKyselykerta] = useState<string | undefined>(
        undefined,
    );
    const effectiveKyselykerta = selectedKyselykerta ?? kyselykertaStart;

    const options: DropDownItem[] =
        availableKyselykertas
            ?.sort(
                (a, b) =>
                    parseISO(b.kyselykerta_alkupvm).getTime() -
                    parseISO(a.kyselykerta_alkupvm).getTime(),
            )
            .map((akk) => {
                const akkNimi = `nimi_${lang}` as keyof AvailableKyselykertas;
                return {
                    value: akk.kyselykerta_alkupvm,
                    name: akk[akkNimi],
                    disabled: !akk[tyyppi as keyof AvailableKyselykertas],
                } as DropDownItem;
            }) ?? [];

    return options.length > 0 ? (
        <div>
            <h2>{t('kyselykerta-valitsin-otsikko')}</h2>
            <div className={styles['dropdown-wrapper']}>
                <DropDownField
                    disabled={options.filter((opt) => !opt.disabled).length < 2}
                    id="vastaajan-tehtavanimike"
                    value={effectiveKyselykerta}
                    label={t('kyselykerta-valitsin-label')}
                    options={options}
                    onChange={(pvm) => setSelectedKyselykerta(pvm)}
                />
            </div>

            <div>
                <button
                    type="button"
                    disabled={
                        !effectiveKyselykerta || availableKyselykertas?.length === 1
                    }
                    onClick={() => {
                        sideEffects?.forEach((effect) => effect());
                        const queryParams = new URLSearchParams(location.search);
                        queryParams.set('alkupvm', effectiveKyselykerta!);
                        navigate(
                            {pathname: location.pathname, search: queryParams.toString()},
                            {replace: true, state: false},
                        );
                    }}
                >
                    {t('kyselykerta-valitsin-siirry')}
                </button>

                <GuardedComponentWrapper roles={{arvo: [ArvoRoles.PAAKAYTTAJA]}}>
                    {csvObservable !== undefined && (
                        <ConfirmationDialog
                            title={t('lataa-aineisto-otsikko')}
                            confirmBtnText={t('lataa-aineisto')}
                            confirm={() => downloadCsv(csvObservable!, csvName!)}
                            content={
                                <>
                                    <p>{t('lataa-aineisto-teksti-1')}</p>
                                    <p>
                                        {`${t('lataa-aineisto-teksti-2')} `}
                                        <a
                                            href={t('lataa-aineisto-ohje-url')}
                                            target="_blank"
                                            rel="noreferrer"
                                        >
                                            {t('lataa-aineisto-ohje')}
                                            <LaunchIcon fontVariant="externalLaunch" />
                                        </a>
                                    </p>
                                </>
                            }
                        >
                            <button
                                type="button"
                                disabled={kyselykertaStart !== effectiveKyselykerta}
                            >
                                {t('lataa-aineisto')}
                            </button>
                        </ConfirmationDialog>
                    )}
                </GuardedComponentWrapper>
            </div>
        </div>
    ) : (
        <span />
    );
}

export default KyselykertaValitsin;
