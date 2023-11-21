import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormLabel from '@mui/material/FormLabel';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import {useTranslation} from 'react-i18next';
import QuestionTypes from '../QuestionType/QuestionTypes';
import InputTypes from './InputTypes';

interface InputTypeProps {
    questionType: QuestionTypes;
    selectedInputType: string;
    handleInputTypeChange: Function;
}

function InputType({
    questionType,
    selectedInputType,
    handleInputTypeChange,
}: InputTypeProps) {
    const {t} = useTranslation(['kysely']);
    const generateOptions = (type: string) => {
        if (type === QuestionTypes.text) {
            return (
                <>
                    <FormControlLabel
                        value={InputTypes.singletext}
                        control={<Radio />}
                        label={t('tekstikentta-label')}
                    />
                    <FormControlLabel
                        value={InputTypes.multiline}
                        control={<Radio />}
                        label={t('monirivinen-tekstikentta-label')}
                    />
                    <FormControlLabel
                        value={InputTypes.numeric}
                        control={<Radio />}
                        label={t('numerokentta-label')}
                    />
                </>
            );
        }
        if (type === QuestionTypes.multi) {
            return (
                <>
                    <FormControlLabel
                        value={InputTypes.radio}
                        control={<Radio />}
                        label={t('valintanapit-label')}
                    />
                    <FormControlLabel
                        value={InputTypes.checkbox}
                        control={<Radio />}
                        label={t('valintaruudut-label')}
                    />
                </>
            );
        }
        if (type === QuestionTypes.matrix) {
            return (
                <>
                    <FormControlLabel
                        value={InputTypes.matrix_radio}
                        control={<Radio />}
                        label={t('valintanappirivi-label')}
                    />
                    <FormControlLabel
                        value={InputTypes.matrix_slider}
                        control={<Radio />}
                        label={t('liukumaskaala-label')}
                    />
                </>
            );
        }
        return null;
    };
    return (
        <FormControl component="fieldset">
            <FormLabel component="legend">{t('kentan-tyyppi')}</FormLabel>
            <RadioGroup
                aria-label="input type"
                name="Input type"
                value={selectedInputType || ''}
                onChange={(e) => handleInputTypeChange(e)}
            >
                {generateOptions(questionType)}
            </RadioGroup>
        </FormControl>
    );
}

export default InputType;
