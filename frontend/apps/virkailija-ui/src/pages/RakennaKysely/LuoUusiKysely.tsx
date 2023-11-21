import {Dispatch, SetStateAction, useContext, useEffect, useState} from 'react';
import {map} from 'rxjs/operators';
import {useLocation} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import FormControl from '@mui/material/FormControl';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import {KyselyType, StatusType, TextType} from '@cscfi/shared/services/Data/Data-service';
import GenericTextField from '@cscfi/shared/components/GenericTextField/GenericTextField';
import {
    arvoPostJsonHttp$,
    PaaIndikaattoriType,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {getQueryParamAsNumber} from '@cscfi/shared/utils/helpers';
import {
    IndikaattoriType,
    virkailijapalveluGetIndikaattoriRyhma$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import UserContext from '../../Context';
import ButtonWithLink from '../../components/ButtonWithLink/ButtonWithLink';
import {
    lomakeTyypitList,
    lomakeTyypitProsessitekijaList,
    lomakeTyypitRakennetekijaList,
} from '../../utils/LomakeTyypit';
import styles from './RakennaKysely.module.css';
import SecondaryIndicators from '../../components/SecondaryIndicators/SecondaryIndicators';

const createNewKysely$ = (
    topic: TextType,
    lomaketyyppi: string,
    paaIndikaattori: PaaIndikaattoriType,
    selectedSecondaryIndicators: IndikaattoriType[],
) =>
    arvoPostJsonHttp$('kysymysryhma', {
        nimi_fi: topic.fi,
        nimi_sv: topic.sv,
        valtakunnallinen: true,
        metatiedot: {
            lomaketyyppi,
            paaIndikaattori,
            sekondaariset_indikaattorit: selectedSecondaryIndicators,
        },
    }).pipe<number>(map((response) => response?.kysymysryhmaid));

interface LuoUusiKyselyProps {
    handleChange: Function;
    setKysely: Dispatch<SetStateAction<KyselyType | null>>;
}

function LuoUusiKysely({handleChange, setKysely}: LuoUusiKyselyProps) {
    const {t} = useTranslation(['rakennakysely']);
    const userInfo = useContext(UserContext);
    const location = useLocation();
    const [groupId, setGroupId] = useState<number>(-1);
    const [indikaattoriLista, setIndikaattoriLista] = useState<IndikaattoriType[]>([]);
    const defaultLomakeTyyppi = lomakeTyypitList[0];
    const defaultProsessiLomaketyyppi = lomakeTyypitProsessitekijaList[0];
    const defaultRakenneLomaketyyppi = lomakeTyypitRakennetekijaList[0];
    const [lomaketyyppi, setLomaketyyppi] = useState<string>(defaultLomakeTyyppi);
    const [indikaattori, setIndikaattori] = useState<string>('');
    const [selectedSecondaryIndicators, setSelectedSecondaryIndicators] = useState<
        IndikaattoriType[]
    >([]);

    const [topic, setTopic] = useState<TextType>({fi: '', sv: ''});

    const kyselytyyppiProsessitekijaList = lomakeTyypitProsessitekijaList?.map(
        (kyselytyyppi) => (
            <MenuItem value={kyselytyyppi} key={kyselytyyppi}>
                {t(kyselytyyppi, {ns: 'yleiset'})}
            </MenuItem>
        ),
    );

    useEffect(() => {
        const groupIdFromUrl = getQueryParamAsNumber(location, 'group');
        if (groupIdFromUrl) {
            setGroupId(groupIdFromUrl);
            virkailijapalveluGetIndikaattoriRyhma$(userInfo!)(groupIdFromUrl).subscribe(
                (indikaattoriRyhmat) => {
                    setIndikaattoriLista(indikaattoriRyhmat[0].indicators);
                    setIndikaattori(indikaattoriRyhmat[0].indicators[0].key);
                    if (indikaattoriRyhmat[0].indicators[0].laatutekija === 'prosessi') {
                        setLomaketyyppi(defaultProsessiLomaketyyppi);
                    } else if (
                        indikaattoriRyhmat[0].indicators[0].laatutekija === 'rakenne'
                    ) {
                        setLomaketyyppi(defaultRakenneLomaketyyppi);
                    }
                },
            );
        }
    }, [defaultProsessiLomaketyyppi, defaultRakenneLomaketyyppi, location, userInfo]);

    const kyselytyyppiRakennetekijaList = lomakeTyypitRakennetekijaList?.map(
        (kyselytyyppi) => (
            <MenuItem value={kyselytyyppi} key={kyselytyyppi}>
                {t(kyselytyyppi, {ns: 'yleiset'})}
            </MenuItem>
        ),
    );

    const onSave = () => {
        const indikaattoriData = {group: groupId, key: indikaattori};
        createNewKysely$(
            topic,
            lomaketyyppi,
            indikaattoriData,
            selectedSecondaryIndicators,
        ).subscribe((kyselyId) => {
            const newKysely = {
                id: kyselyId,
                kysymykset: [],
                topic,
                status: StatusType.luonnos,
                lomaketyyppi,
                paaIndikaattori: indikaattoriData,
                sekondaariset_indikaattorit: selectedSecondaryIndicators,
            };
            setKysely(newKysely);
        });
        handleChange(topic);
    };

    // if url is missing the group id, no indicators or questionnaire types can be set
    if (groupId < 0) {
        return <p>{t('luouusi-parametri-puuttuu')}</p>;
    }
    const tyyppi = lomaketyyppi?.substring(lomaketyyppi.lastIndexOf('_') + 1);

    return (
        <>
            <h1>{t('luouusi-otsikko')}</h1>
            <div className={styles['topic-container']}>
                <div>
                    <GenericTextField
                        value={topic.fi}
                        fullWidth
                        autoComplete={false}
                        autoFocus
                        label={t('luouusi-label-nimi-fi')}
                        required
                        showLabel
                        onChange={(newValue: string) =>
                            setTopic((prevState) => ({...prevState, fi: newValue}))
                        }
                    />
                    <GenericTextField
                        value={topic.sv}
                        fullWidth
                        autoComplete={false}
                        autoFocus
                        label={t('luouusi-label-nimi-sv')}
                        showLabel
                        onChange={(newValue: string) =>
                            setTopic((prevState) => ({...prevState, sv: newValue}))
                        }
                    />
                </div>
            </div>
            {indikaattoriLista.length > 0 && (
                <FormControl fullWidth>
                    <div>
                        <div>
                            <label
                                htmlFor="mainIndicator"
                                className="label-for-inputfield"
                            >
                                {t('luouusi-label-indikaattori')} *
                            </label>
                            <Select
                                id="mainIndicator"
                                value={indikaattori || indikaattoriLista[0].key}
                                onChange={(e) => {
                                    setIndikaattori(e.target.value);
                                }}
                            >
                                {indikaattoriLista.map((ind: IndikaattoriType) => (
                                    <MenuItem value={ind.key} key={ind.key}>
                                        {t(ind.key, {ns: 'indik'})}
                                    </MenuItem>
                                ))}
                            </Select>
                        </div>
                    </div>
                </FormControl>
            )}
            <FormControl fullWidth className={styles.secondaryIndicatorsWrapper}>
                <div>
                    <SecondaryIndicators
                        setSelectedSecondaryIndicators={setSelectedSecondaryIndicators}
                        selectedSecondaryIndicators={selectedSecondaryIndicators}
                        lomaketyyppi={tyyppi}
                        paaIndikaattori={indikaattori}
                    />
                </div>
            </FormControl>
            <FormControl fullWidth>
                <div>
                    <label htmlFor="questionnaireType" className="label-for-inputfield">
                        {t('luouusi-label-lomaketyyppi')} *
                    </label>
                    <Select
                        id="questionnaireType"
                        value={lomaketyyppi}
                        onChange={(e) => setLomaketyyppi(e.target.value)}
                    >
                        {indikaattoriLista.length > 0 &&
                            indikaattoriLista[0].laatutekija === 'prosessi' &&
                            kyselytyyppiProsessitekijaList}
                        {indikaattoriLista.length > 0 &&
                            indikaattoriLista[0].laatutekija === 'rakenne' &&
                            kyselytyyppiRakennetekijaList}
                    </Select>
                </div>
            </FormControl>

            <div className="button-container">
                <ButtonWithLink
                    className="secondary"
                    linkTo="/indikaattorit"
                    linkText={t('luouusi-painike-peruuta')}
                />
                <button type="button" onClick={onSave} disabled={topic.fi.trim() === ''}>
                    {t('luouusi-painike-luo-lomakepohja')}
                </button>
            </div>
        </>
    );
}

export default LuoUusiKysely;
