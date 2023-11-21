import {useTranslation} from 'react-i18next';
import {Control, FieldValues} from 'react-hook-form';
import {ReactElement} from 'react';
import {KyselyType, KysymysType, TextType} from '../../services/Data/Data-service';
import InputTypes from '../InputType/InputTypes';
import SingleField from './FormFields/SingleField/SingleField';
import MultiOptionField from './FormFields/MultiOptionField/MultiOptionField';
import MatrixField from './FormFields/MatrixField/MatrixField';
import TitleField from './FormFields/TitleField/TitleField';
import styles from './Form.module.css';

interface FormProps {
    kysely: KyselyType;
    editable?: Boolean;
    errors: FieldValues;
    isSubmitting: boolean;
    control: Control;
    vastaajaUi: boolean;
    renderFormFieldActions?: (
        id: number,
        previousid: number,
        nextid: number,
    ) => ReactElement;
}

function Form({
    kysely,
    editable = false,
    errors,
    isSubmitting = false,
    control,
    vastaajaUi,
    renderFormFieldActions,
}: FormProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['error', 'form', 'indik']);
    const langKey = lang as keyof TextType;

    const renderKysymykset = (kysymykset: KysymysType[]) =>
        kysymykset.map((kysymys, index) => {
            const previous = kysymykset[index - 1];
            const next = kysymykset[index + 1];

            const {inputType, id, title, required, description} = kysymys;
            const {hidden} = required ? {hidden: false} : kysymys;
            const kyselyKysymysId = `${kysely.id}_${id}`;
            let element: ReactElement;
            switch (inputType) {
                case InputTypes.singletext:
                case InputTypes.multiline:
                case InputTypes.numeric:
                    element = (
                        <SingleField
                            type={inputType as InputTypes}
                            id={kyselyKysymysId}
                            required={required || false}
                            title={title?.[langKey]}
                            description={description?.[langKey]}
                            fieldErrors={errors[kyselyKysymysId]}
                            control={control}
                        />
                    );
                    break;
                case InputTypes.radio:
                case InputTypes.checkbox: {
                    const {answerOptions} = kysymys;
                    element = (
                        <MultiOptionField
                            id={kyselyKysymysId}
                            required={required || false}
                            title={title?.[langKey]}
                            description={description?.[langKey]}
                            answerOptions={answerOptions}
                            type={inputType}
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
                            hidden={hidden}
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
                    console.log(`Error: Invalid Field input type: ${inputType}`);
                    element = (
                        <div key={id}>
                            <span>{`${t(
                                'invalid-field-input-type',
                            )}: (${inputType})`}</span>
                        </div>
                    );
            }

            if (hidden && !editable) {
                return null;
            }

            return (
                <div
                    key={kyselyKysymysId}
                    className={
                        // eslint-disable-next-line no-nested-ternary
                        hidden
                            ? `${styles.KysymysFieldContainer} ${styles.hidden}`
                            : editable
                            ? `${styles.KysymysFieldContainer} ${styles.editable}`
                            : styles.KysymysFieldContainer
                    }
                >
                    {hidden && (
                        <p className={`overall-error ${styles.KysymysHiddenIndicator}`}>
                            {t('form:tama-kentta-on-piilotettu')}
                        </p>
                    )}
                    <div className={styles.KysymysContent}>
                        {element}
                        {editable && renderFormFieldActions(id, previous?.id, next?.id)}
                    </div>
                </div>
            );
        });
    const {kysymykset} = kysely;
    return (
        <>
            {!editable && (
                <div className={styles.Indikaattorit}>
                    <p>{t('indik:johdanto')}</p>
                    <p>{t(`indik:desc_${kysely.paaIndikaattori?.key}`)}</p>
                </div>
            )}
            {renderKysymykset(kysymykset)}
            {vastaajaUi && (
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
                    />
                </div>
            )}
        </>
    );
}

export default Form;
