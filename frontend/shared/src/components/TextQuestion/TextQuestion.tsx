import {Dispatch, SetStateAction} from 'react';
import {useTranslation} from 'react-i18next';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import LanguageTitle from '../LanguageTitle/LanguageTitle';
import GenericText from '../GenericText/GenericText';
import DescriptionText from '../DescriptionText/DescriptionText';

interface TextQuestionProps {
    title: TextType;
    description: TextType;
    handleChange: (changeFromSubComponent: object) => void;
    showEnglish: boolean;
    ruotsiVaiEnglantiValittu: string;
    setRuotsiVaiEnglantiValittu: Dispatch<SetStateAction<string | null>>;
}

function TextQuestion({
    title,
    description,
    handleChange,
    showEnglish,
    ruotsiVaiEnglantiValittu,
    setRuotsiVaiEnglantiValittu,
}: TextQuestionProps) {
    const {t} = useTranslation(['yleiset']);
    const onTitleChange = (valueFromInputField: TextType) => {
        handleChange({title: valueFromInputField});
    };
    const onDescriptionChange = (valueFromInputField: TextType) => {
        handleChange({description: valueFromInputField});
    };

    return (
        <>
            <LanguageTitle
                showEnglish={showEnglish}
                ruotsiVaiEnglantiValittu={ruotsiVaiEnglantiValittu}
                setRuotsiVaiEnglantiValittu={setRuotsiVaiEnglantiValittu}
            />

            <GenericText
                value={title}
                fullWidth
                autoComplete={false}
                autoFocus
                label={t('otsikko-label')}
                onChange={onTitleChange}
                required
                showEnglish={showEnglish}
                ruotsiVaiEnglantiValittu={ruotsiVaiEnglantiValittu}
            />
            <DescriptionText
                value={description}
                onChange={onDescriptionChange}
                showEnglish={showEnglish}
                ruotsiVaiEnglantiValittu={ruotsiVaiEnglantiValittu}
            />
        </>
    );
}

export default TextQuestion;
