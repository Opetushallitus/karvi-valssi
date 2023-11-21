import {useTranslation} from 'react-i18next';
import {useEffect, useState} from 'react';
import {AvailableKyselykertas} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {useLocation, useNavigate} from 'react-router-dom';
import {parseISO} from 'date-fns';
import DropDownField, {
    DropDownItem,
} from '@cscfi/shared/components/DropDownField/DropDownField';
import styles from '../../pages/Raportointi/raportit.module.css';

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
}

function KyselykertaValitsin({
    availableKyselykertas,
    kyselykertaStart,
    tyyppi = ValitsinTyyppi.raportti,
    sideEffects = [],
}: KyselykertaValitsinProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['raportointi']);
    const location = useLocation();
    const navigate = useNavigate();

    const [selectedKyselykerta, setSelectedKyselykerta] = useState<string | undefined>(
        kyselykertaStart,
    );

    useEffect(() => {
        if (!selectedKyselykerta) {
            setSelectedKyselykerta(kyselykertaStart);
        }
    }, [kyselykertaStart, selectedKyselykerta]);

    return availableKyselykertas && availableKyselykertas.length > 1 ? (
        <div>
            <h2>{t('kyselykerta-valitsin-otsikko')}</h2>
            <div className={styles['dropdown-wrapper']}>
                <DropDownField
                    id="vastaajan-tehtavanimike"
                    value={selectedKyselykerta}
                    label={t('kyselykerta-valitsin-label')}
                    options={availableKyselykertas
                        .sort(
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
                        })}
                    onChange={(pvm) => setSelectedKyselykerta(pvm)}
                />
            </div>
            <div>
                <button
                    type="button"
                    disabled={!selectedKyselykerta}
                    onClick={() => {
                        sideEffects?.forEach((effect) => effect());
                        const queryParams = new URLSearchParams(location.search);
                        queryParams.set('alkupvm', selectedKyselykerta!);
                        navigate(
                            {
                                pathname: location.pathname,
                                search: queryParams.toString(),
                            },
                            {replace: true, state: false},
                        );
                    }}
                >
                    {t('kyselykerta-valitsin-siirry')}
                </button>
            </div>
        </div>
    ) : (
        <span />
    );
}

export default KyselykertaValitsin;
