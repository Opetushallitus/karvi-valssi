import {useTranslation} from 'react-i18next';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import LanguageTitle from '../LanguageTitle/LanguageTitle';
import GenericText from '../GenericText/GenericText';
import DescriptionText from '../DescriptionText/DescriptionText';

interface TextQuestionProps {
    title: TextType;
    description: TextType;
    handleChange: Function;
}

function TextQuestion({title, description, handleChange}: TextQuestionProps) {
    const {t} = useTranslation(['yleiset']);
    const onTitleChange = (valueFromInputField: TextType) => {
        handleChange({title: valueFromInputField});
    };
    const onDescriptionChange = (valueFromInputField: TextType) => {
        handleChange({description: valueFromInputField});
    };

    return (
        <>
            <LanguageTitle />

            <GenericText
                value={title}
                fullWidth
                autoComplete={false}
                autoFocus
                label={t<string>('otsikko-label')}
                onChange={onTitleChange}
                required
            />
            <DescriptionText value={description} onChange={onDescriptionChange} />
        </>
    );
}

export default TextQuestion;
