import React, {Dispatch, SetStateAction, useContext, useEffect, useState} from 'react';
import {map} from 'rxjs/operators';
import {useLocation} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import FormControl from '@mui/material/FormControl';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import {
    KyselyType,
    PaaindikaattoriType,
    SekondaarinenIndikaattoriType,
    StatusType,
    TextType,
} from '@cscfi/shared/services/Data/Data-service';
import GenericTextField from '@cscfi/shared/components/GenericTextField/GenericTextField';
import {arvoPostJsonHttp$} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {getQueryParamAsNumber} from '@cscfi/shared/utils/helpers';
import {virkailijapalveluGetIndikaattoriRyhma$} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import LomakeTyyppi, {
    lomakeTyypitProsessitekijaList,
    lomakeTyypitRakennetekijaList,
    lomakeTyypitKansallisetList,
} from '@cscfi/shared/utils/LomakeTyypit';
import UserContext from '../../Context';
import ButtonWithLink from '../../components/ButtonWithLink/ButtonWithLink';
import styles from './RakennaKysely.module.css';
import SecondaryIndicators from '../../components/SecondaryIndicators/SecondaryIndicators';

const createNewKysely$ = (
    topic: TextType,
    lomaketyyppi: string,
    paaIndikaattori: PaaindikaattoriType,
    selectedSecondaryIndicators: SekondaarinenIndikaattoriType[],
) =>
    arvoPostJsonHttp$('kysymysryhma', {
        nimi_fi: topic.fi,
        nimi_sv: topic.sv,
        nimi_en: topic.en,
        valtakunnallinen: true,
        metatiedot: {
            lomaketyyppi,
            paaIndikaattori,
            sekondaariset_indikaattorit: selectedSecondaryIndicators,
        },
    }).pipe<number>(map((response) => response?.kysymysryhmaid));

interface LuoUusiKyselyProps {
    handleChange: (value: ((prevState: TextType) => TextType) | TextType) => void;
    setKysely: Dispatch<SetStateAction<KyselyType | null>>;
}

function LuoUusiKysely({handleChange, setKysely}: LuoUusiKyselyProps) {
    const {t} = useTranslation(['rakennakysely']);
    const userInfo = useContext(UserContext);
    const location = useLocation();
    const [indikaattoriLista, setIndikaattoriLista] = useState<
        SekondaarinenIndikaattoriType[]
    >([]);
    const defaultProsessiLomaketyyppi = lomakeTyypitProsessitekijaList[0];
    const defaultRakenneLomaketyyppi = lomakeTyypitRakennetekijaList[0];
    const defaultKansallinenLomaketyppi = lomakeTyypitKansallisetList[0];
    const [lomaketyyppi, setLomaketyyppi] = useState<string>('');
    const [indikaattori, setIndikaattori] = useState<string>('');
    const [selectedSecondaryIndicators, setSelectedSecondaryIndicators] = useState<
        SekondaarinenIndikaattoriType[]
    >([]);

    const [vapaaehtoisetKieletVisible, setVapaaehtoisetKieletVisible] =
        useState<boolean>(false);
    const [englantiNimiVisible, setEnglantiNimiVisible] = useState<boolean>(false);
    const [vapaaehtoisetKieletList, setVapaaehtoisetKieletList] = useState<string[]>([
        t('toimintakieli-en', {ns: 'raportointi'}),
    ]);
    const [vapaaehtoinenKieli, setVapaaehtoinenKieli] = useState<string>(
        vapaaehtoisetKieletList[0],
    );

    const groupIdFromUrl = getQueryParamAsNumber(location, 'group');
    // group 3000 (national questionnaire) warrants for all the indicators
    const nationalQuestionnaire = groupIdFromUrl === 3000;
    const groupId = groupIdFromUrl ?? -1;

    const [topic, setTopic] = useState<TextType>({fi: '', sv: '', en: ''});

    const kyselytyyppiList = (lomakeTyyppiList: LomakeTyyppi[]) =>
        lomakeTyyppiList?.map((kyselytyyppi) => (
            <MenuItem value={kyselytyyppi} key={kyselytyyppi}>
                {t(kyselytyyppi, {ns: 'yleiset'})}
            </MenuItem>
        ));

    useEffect(() => {
        if (groupIdFromUrl) {
            const subscription = virkailijapalveluGetIndikaattoriRyhma$(userInfo!)(
                !nationalQuestionnaire ? groupIdFromUrl : undefined,
            ).subscribe((indikaattoriRyhmat) => {
                const initialIndikaattoriNimet = indikaattoriRyhmat.flatMap(
                    (ir) => ir.indicators,
                );
                const kansallinenIndikaattori = initialIndikaattoriNimet.find(
                    (nimi) => nimi.group_id === 3000,
                );
                // kansallinenIndikaattori to the top of the list, if it exists.
                const indikaattoriNimet = !kansallinenIndikaattori
                    ? initialIndikaattoriNimet
                    : [
                          kansallinenIndikaattori,
                          ...initialIndikaattoriNimet.filter(
                              (ii) => ii.group_id !== 3000,
                          ),
                      ];
                setIndikaattoriLista(indikaattoriNimet);
                setIndikaattori(indikaattoriNimet[0].key);

                if (nationalQuestionnaire) {
                    setLomaketyyppi(defaultKansallinenLomaketyppi);
                } else if (
                    indikaattoriRyhmat[0].indicators[0].laatutekija === 'prosessi'
                ) {
                    setLomaketyyppi(defaultProsessiLomaketyyppi);
                } else if (
                    indikaattoriRyhmat[0].indicators[0].laatutekija === 'rakenne'
                ) {
                    setLomaketyyppi(defaultRakenneLomaketyyppi);
                }
            });
            return () => subscription.unsubscribe();
        }
    }, [
        defaultKansallinenLomaketyppi,
        defaultProsessiLomaketyyppi,
        defaultRakenneLomaketyyppi,
        groupIdFromUrl,
        location,
        nationalQuestionnaire,
        userInfo,
    ]);

    function updateVapaaehtoisetKieletList() {
        setVapaaehtoisetKieletList(
            vapaaehtoisetKieletList.filter(
                (item) => item !== t('toimintakieli-en', {ns: 'raportointi'}),
            ),
        );
    }

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

    // if url is missing the group ID, no indicators or questionnaire types can be set.
    if (groupId < 0) {
        return <p>{t('luouusi-parametri-puuttuu')}</p>;
    }

    function addVapaaehtoinenKieli() {
        if (
            vapaaehtoinenKieli &&
            vapaaehtoinenKieli === t('toimintakieli-en', {ns: 'raportointi'})
        ) {
            updateVapaaehtoisetKieletList();
            setEnglantiNimiVisible(true);
            setVapaaehtoisetKieletVisible(false);
        }
    }

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
                        required
                        showLabel
                        onChange={(newValue: string) =>
                            setTopic((prevState) => ({...prevState, sv: newValue}))
                        }
                    />

                    {englantiNimiVisible && (
                        <GenericTextField
                            value={topic.en}
                            fullWidth
                            autoComplete={false}
                            autoFocus
                            label={t('luouusi-label-nimi-en')}
                            required
                            showLabel
                            onChange={(newValue: string) =>
                                setTopic((prevState) => ({...prevState, en: newValue}))
                            }
                        />
                    )}
                </div>
            </div>

            {!vapaaehtoisetKieletVisible && (
                <button
                    type="button"
                    onClick={() =>
                        setVapaaehtoisetKieletVisible(!vapaaehtoisetKieletVisible)
                    }
                    className={styles.showVapaaehtoisetKieletButton}
                >
                    {`+ ${t('lisaa-kielia')}`}
                </button>
            )}
            {vapaaehtoisetKieletVisible && (
                <FormControl fullWidth>
                    <div>
                        <div>
                            <label
                                htmlFor="vapaaehtoisetKielet"
                                className="label-for-inputfield"
                            >
                                {t('valitse-kielet')}
                            </label>
                            <div className={styles.addWrapper}>
                                <Select
                                    id="vapaaehtoinenKieli"
                                    value={
                                        vapaaehtoinenKieli || vapaaehtoisetKieletList[0]
                                    }
                                    defaultValue={vapaaehtoisetKieletList[0]}
                                    onClick={(e) => {
                                        if (e?.target?.textContent?.length > 0) {
                                            setVapaaehtoinenKieli(e.target.textContent);
                                        }
                                    }}
                                >
                                    {vapaaehtoisetKieletList.map((item) => (
                                        <MenuItem value={item} key={item}>
                                            {item}
                                        </MenuItem>
                                    ))}
                                </Select>
                                <button
                                    className="small"
                                    type="button"
                                    disabled={!vapaaehtoisetKieletVisible}
                                    onClick={() => {
                                        addVapaaehtoinenKieli();
                                    }}
                                    style={{marginLeft: '0.5rem'}}
                                >
                                    {t('tallenna', {ns: 'kysely'})}
                                </button>
                            </div>
                        </div>
                    </div>
                </FormControl>
            )}
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
                                {indikaattoriLista.map(
                                    (ind: SekondaarinenIndikaattoriType) => (
                                        <MenuItem value={ind.key} key={ind.key}>
                                            {t(ind.key, {ns: 'indik'})}
                                        </MenuItem>
                                    ),
                                )}
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
                        lomaketyyppi={lomaketyyppi}
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
                            kyselytyyppiList(lomakeTyypitProsessitekijaList)}
                        {indikaattoriLista.length > 0 &&
                            indikaattoriLista[0].laatutekija === 'rakenne' &&
                            kyselytyyppiList(lomakeTyypitRakennetekijaList)}
                        {indikaattoriLista.length > 0 &&
                            indikaattoriLista[0].laatutekija === 'kansallinen' &&
                            kyselytyyppiList(lomakeTyypitKansallisetList)}
                    </Select>
                </div>
            </FormControl>

            <div className="button-container">
                <ButtonWithLink
                    className="secondary"
                    linkTo="/indikaattorit"
                    linkText={t('luouusi-painike-peruuta')}
                />
                <button
                    type="button"
                    onClick={onSave}
                    disabled={
                        topic.fi.trim() === '' ||
                        topic.sv.trim() === '' ||
                        (englantiNimiVisible && topic.en.trim() === '')
                    }
                >
                    {t('luouusi-painike-luo-lomakepohja')}
                </button>
            </div>
        </>
    );
}

export default LuoUusiKysely;
