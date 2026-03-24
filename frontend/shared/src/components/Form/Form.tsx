import {useTranslation} from 'react-i18next';
import {Control, FieldValues, useWatch} from 'react-hook-form';
import {MutableRefObject, ReactElement, useEffect, useMemo, useState} from 'react';
import {getFollowupNotSatisfied} from '@cscfi/shared/utils/helpers';
import {MaxLengths} from '@cscfi/shared/utils/validators';
import Button from '@mui/material/Button';
import Add from '@mui/icons-material/Add';
import Remove from '@mui/icons-material/Remove';
import {isEqualWith, toNumber} from 'lodash';
import ViewIndicators from '../ViewIndicators/ViewIndicators';
import {vastauspalveluGetMatrixScales$} from '../../services/Vastauspalvelu-api/Vastauspalvelu-api-service';
import {virkailijapalveluGetMatrixScales$} from '../../services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {
    HiddenType,
    KyselyType,
    KysymysType,
    MatrixType,
    TextType,
} from '../../services/Data/Data-service';
import InputTypes from '../InputType/InputTypes';
import SingleField from './FormFields/SingleField/SingleField';
import MultiOptionField from './FormFields/MultiOptionField/MultiOptionField';
import DropdownField from './FormFields/DropdownField/DropdownField';
import MatrixField from './FormFields/MatrixField/MatrixField';
import TitleField from './FormFields/TitleField/TitleField';
import styles from './Form.module.css';

interface FormProps {
    kysely: KyselyType;
    editable?: boolean;
    errors: FieldValues;
    isSubmitting: boolean;
    control: Control;
    vastaajaUi: boolean;
    renderFormFieldActions?: (
        id: number,
        previousid: number,
        nextid: number,
    ) => ReactElement;
    handleTogglePagebreak?: (kysymys: KysymysType) => void;
    tempAnswers?: () => void;
    onLastPage: boolean;
    setLastPage: (value: boolean) => void;
    focusTitleRef?: MutableRefObject<HTMLDivElement>;
    language?: string;
}

function isHidden(req: boolean, follNotSat: boolean, kysymys: KysymysType): HiddenType {
    if (kysymys.hidden === true) return HiddenType.hidden;
    if (req || Object.keys(kysymys.followupTo || {}).length === 0)
        return HiddenType.notHidden;
    if (follNotSat) return HiddenType.hiddenByCondition;
    return HiddenType.notHidden;
}

function Form({
    kysely,
    editable = false,
    errors,
    isSubmitting = false,
    control,
    vastaajaUi,
    renderFormFieldActions,
    handleTogglePagebreak,
    tempAnswers,
    onLastPage,
    setLastPage,
    focusTitleRef,
    language,
}: FormProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['error', 'form', 'indik']);
    const langKey = language ? language : (lang as keyof TextType);

    const [matrixTypes, setMatrixTypes] = useState<Array<MatrixType>>(null);

    // Käyttäjän valitsema sivu; jos tämä on null, pudotaan virhesivuun tai 0:aan
    const [userPage, setUserPage] = useState<number | null>(null);

    const {kysymykset} = kysely;
    const nPages = kysymykset.at(-1).page ?? 0;

    const watchValues = useWatch({control});

    // Hae matriisiasteikot; siivoa tilaus unmountissa
    useEffect(() => {
        const scalesObservable = vastaajaUi
            ? vastauspalveluGetMatrixScales$
            : virkailijapalveluGetMatrixScales$;
        const sub = scalesObservable().subscribe((mt) => {
            setMatrixTypes(mt);
            if (tempAnswers) {
                tempAnswers();
            }
        });
        return () => sub.unsubscribe();
    }, [kysely.kysymykset, tempAnswers, vastaajaUi]);

    // Johda ensimmäinen virhesivu renderiin (ei setStatea efektissä)
    const errorPage = useMemo(() => {
        const first = Object.entries(errors).at(0);
        if (!first) return null;

        const errKysymysId = first[0].split('_')[1];
        if (!errKysymysId) return null; // esim. jos virhe on sähköpostikentässä tms.

        const errIdNum = toNumber(errKysymysId);

        // 1) suora osuma kysymykseen tai sen matrix-alaelementtiin
        const kys =
            kysymykset.find(
                (kysymys) =>
                    kysymys.id === errIdNum ||
                    kysymys.matrixQuestions.find((mk) => mk.id === errIdNum),
            ) ??
            // 2) followup-kysymys
            kysymykset
                .flatMap((kysymys: KysymysType) =>
                    Object.values(kysymys.followupQuestions),
                )
                .find((fq) => fq.id.toString() === errKysymysId);

        return kys?.page ?? 0;
    }, [errors, kysymykset]);

    // Näytettävä sivu: käyttäjän valinta -> virhesivu -> 0
    const currentPage = userPage ?? errorPage ?? 0;

    // Scrollaa ensimmäiseen virheeseen (jos sellainen on) ja päivitä "on viimeisellä sivulla" -tieto
    useEffect(() => {
        if (Object.entries(errors)?.at(0)) {
            const element = document.getElementById(Object.entries(errors).at(0)[0]);
            element?.scrollIntoView({behavior: 'smooth', block: 'center'});
            element?.focus?.();
        }
        setLastPage(nPages === 0 || currentPage === nPages);
    }, [currentPage, errors, nPages, setLastPage]);

    function focusToPageTitle() {
        focusTitleRef?.current?.scrollIntoView({behavior: 'smooth', block: 'start'});
        focusTitleRef?.current?.focus?.();
    }

    const pagebreakIndicator = (
        pagebreak: boolean,
        current: KysymysType,
        next: KysymysType | undefined,
    ) => {
        if (next === undefined) return null;
        return pagebreak ? (
            <div className={styles.pagebreak}>
                <hr />
                {t('form:sivunvaihto')}
                <hr className={styles.rightHr} />
                <Button
                    onClick={() => handleTogglePagebreak(current)}
                    className={`link-alike ${styles['pagebreak-button']}`}
                >
                    {t('form:poista-sivunvaihto')}
                    <Remove />
                </Button>
            </div>
        ) : (
            <Button
                onClick={() => handleTogglePagebreak(current)}
                className={`link-alike ${styles['pagebreak-button']}`}
            >
                {t('form:lisaa-sivunvaihto')}
                <Add />
            </Button>
        );
    };

    const clampPage = (p: number) => Math.min(Math.max(0, p), nPages);

    const pageSwitchButtons = (lower = false) => (
        // Upper row option unused but preserved for if it will be wanted.
        <div
            className={
                styles[
                    lower ? 'page-switch-container-lower' : 'page-switch-container-upper'
                ]
            }
        >
            <Button
                className="small"
                onClick={() => {
                    setUserPage(clampPage(currentPage - 1));
                    focusToPageTitle();
                }}
                disabled={currentPage === 0}
                onFocus={(e) => (e.target as HTMLButtonElement).blur()}
            >
                {t('form:edellinen-sivu')}
            </Button>
            <Button
                className="small"
                onClick={() => {
                    setUserPage(clampPage(currentPage + 1));
                    focusToPageTitle();
                }}
                disabled={currentPage === nPages}
                onFocus={(e) => (e.target as HTMLButtonElement).blur()}
            >
                {t('form:seuraava-sivu')}
            </Button>
            <span className={styles['page-indicator']}>
                {t('form:sivu')} {`${currentPage + 1}/${nPages + 1}`}
            </span>
        </div>
    );

    const renderKysymykset = (rKysymykset: KysymysType[], currPage: number) =>
        rKysymykset.map((kysymys, index) => {
            const previous = rKysymykset[index - 1];
            const next = rKysymykset[index + 1];
            const {inputType, id, title, required, description, pagebreak, page} =
                kysymys;

            const onCurrentPage = isEqualWith(page, currPage);
            const kyselyKysymysId = `${kysely.id}_${id}`;

            // will be true only if there is a follow-up, and it is not true.
            const followUpNotSatisfied = getFollowupNotSatisfied(
                kysely.id,
                kysymys,
                false,
                watchValues,
            );
            const hidden: HiddenType = isHidden(
                !!required,
                followUpNotSatisfied,
                kysymys,
            );
            if (hidden && !editable) return null;

            let element: ReactElement;

            switch (inputType) {
                case InputTypes.singletext:
                case InputTypes.multiline:
                case InputTypes.numeric:
                    element = (
                        <SingleField
                            type={inputType as InputTypes}
                            id={kyselyKysymysId}
                            required={required ?? false}
                            title={title?.[langKey]}
                            description={description?.[langKey]}
                            fieldErrors={errors[kyselyKysymysId]}
                            control={control}
                            maxLength={MaxLengths.vastausString}
                        />
                    );
                    break;

                case InputTypes.radio:
                case InputTypes.checkbox: {
                    const {answerOptions, followupQuestions} = kysymys;
                    element = (
                        <MultiOptionField
                            id={kyselyKysymysId}
                            required={required ?? false}
                            title={title?.[langKey]}
                            description={description?.[langKey]}
                            answerOptions={answerOptions}
                            followupQuestions={followupQuestions}
                            type={inputType}
                            fieldErrors={errors[kyselyKysymysId]}
                            control={control}
                            hidden={hidden}
                            language={language}
                        />
                    );
                    break;
                }

                case InputTypes.dropdown: {
                    const {answerOptions} = kysymys;
                    element = (
                        <DropdownField
                            id={kyselyKysymysId}
                            required={required ?? false}
                            title={title?.[langKey]}
                            description={description?.[langKey]}
                            answerOptions={answerOptions}
                            fieldErrors={errors[kyselyKysymysId]}
                            control={control}
                            hidden={hidden}
                        />
                    );
                    break;
                }

                case InputTypes.matrix_slider:
                case InputTypes.matrix_radio: {
                    const {matrixQuestions} = kysymys;
                    element = (
                        <MatrixField
                            id={kysely.id.toString()}
                            title={title?.[langKey]}
                            description={description?.[langKey]}
                            questions={matrixQuestions}
                            type={inputType}
                            fieldErrors={errors}
                            isSubmitting={isSubmitting}
                            control={control}
                            matrixTypes={matrixTypes!}
                            editable={editable}
                            language={language}
                        />
                    );
                    break;
                }

                case InputTypes.statictext: {
                    element = (
                        <TitleField
                            title={title?.[langKey]}
                            description={description?.[langKey]}
                        />
                    );
                    break;
                }

                default:
                    console.warn(`Error: Invalid Field input type: ${inputType}`);
                    element = (
                        <div key={id}>
                            <span>{`${t('invalid-field-input-type')}: (${inputType})`}</span>
                        </div>
                    );
            }

            return (
                <div
                    key={kyselyKysymysId}
                    className={styles.KysymysFieldContainerWrapper}
                >
                    <div
                        data-testid={`kysymysid-${kyselyKysymysId}`}
                        className={`${styles.KysymysFieldContainer} ${hidden ? styles.hidden : ''} ${
                            editable ? styles.editable : ''
                        }`}
                        hidden={!onCurrentPage && !editable}
                    >
                        {hidden ? (
                            <p
                                className={`overall-error ${styles.KysymysHiddenIndicator}`}
                            >
                                {hidden === HiddenType.hidden &&
                                    t('form:tama-kentta-on-piilotettu')}
                                {hidden === HiddenType.hiddenByCondition &&
                                    t('form:tama-kentta-on-piilotettu-ehdollisesti')}
                            </p>
                        ) : null}
                        <div className={styles.KysymysContent}>
                            {element}
                            {editable &&
                                renderFormFieldActions(id, previous?.id, next?.id)}
                        </div>
                    </div>
                    {editable && pagebreakIndicator(pagebreak, kysymys, next)}
                </div>
            );
        });

    return (
        <>
            {!editable && currentPage === 0 && (
                <ViewIndicators
                    paaindikaattori={kysely.paaIndikaattori}
                    muutIndikaattorit={kysely.sekondaariset_indikaattorit}
                    language={language}
                />
            )}
            {/* {!editable && nPages !== 0 && pageSwitchButtons()} */}
            {matrixTypes && renderKysymykset(kysymykset, currentPage)}
            {!editable && nPages !== 0 && pageSwitchButtons(true)}
            {vastaajaUi && onLastPage && (
                <div className={styles.EmailField}>
                    <SingleField
                        type={InputTypes.email}
                        descriptionDefaultOpen
                        description={t('form:haluatko-vastaukset-sahkopostiisi-info')}
                        id="userEmail"
                        required={false}
                        title={t('form:haluatko-vastaukset-sahkopostiisi')}
                        fieldErrors={errors.userEmail}
                        control={control}
                        maxLength={MaxLengths.email}
                        customErrorMessages={{
                            maxLength: t('form:sahkoposti-maksimipituus', {
                                maxLength: MaxLengths.email,
                            }),
                        }}
                    />
                </div>
            )}
        </>
    );
}

export default Form;
