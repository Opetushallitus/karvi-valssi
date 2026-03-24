import {useState} from 'react';
import {useTranslation} from 'react-i18next';
import AddIcon from '@mui/icons-material/Add';
import Button from '@mui/material/Button';
import RemoveIcon from '@mui/icons-material/Remove';
import {FormControlLabel, Grid} from '@mui/material';
import Checkbox from '@mui/material/Checkbox';
import DropDownField, {
    DropDownItem,
} from '@cscfi/shared/components/DropDownField/DropDownField';
import {
    FollowupDataType,
    FollowupQuestionsType,
    KysymysType,
    TextType,
} from '@cscfi/shared/services/Data/Data-service';
import InputTypes from '@cscfi/shared/components/InputType/InputTypes';
import styles from './FollowupQuestion.module.css';

interface DescriptionTextProps {
    disabled?: boolean;
    followUpData: FollowupQuestionsType;
    optionId: number;
    onChange: (idx: number, kysymys: FollowupDataType) => void;
    kysymykset: KysymysType[];
}

function FollowupQuestion({
    disabled = false,
    followUpData,
    optionId,
    onChange,
    kysymykset,
}: DescriptionTextProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['kysely']);
    const langKey = lang as keyof TextType;

    const kyselynKysymystenIdt = kysymykset?.map((k) => k.id) as number[];

    const instaChecked = (): number => {
        if (
            followUpData?.[optionId] &&
            ([-1, -2].includes(followUpData[optionId].id) ||
                !kyselynKysymystenIdt.includes(followUpData[optionId].id))
        ) {
            if (followUpData[optionId].inputType === InputTypes.singletext) return -1;
            if (followUpData[optionId].inputType === InputTypes.numeric) return -2;
        }
        return 0;
    };

    const dropValue = () => {
        if (
            followUpData?.[optionId] &&
            kyselynKysymystenIdt.includes(followUpData[optionId].id)
        ) {
            return followUpData[optionId].id;
        }
        return 0;
    };

    const [show, setShow] = useState(instaChecked() || dropValue() > 0);
    const [insta, setInsta] = useState<number>(instaChecked());

    const handleFolloupChange = (
        checked: boolean,
        kysymysid: number,
        inputType: InputTypes,
    ) => {
        onChange(optionId, {kysymysid: checked ? kysymysid : null, inputType});

        if (![-1, -2].includes(kysymysid) || !kyselynKysymystenIdt.includes(kysymysid)) {
            setInsta(checked ? kysymysid : 0);
        } else {
            setInsta(0);
        }
    };

    const toggleShow = () => {
        if (show) {
            handleFolloupChange(false, null, null);
            setShow(!show);
        }
        setShow(!show);
    };

    const followUpOptions = () => {
        const opts = kysymykset.map(
            (kysymys) =>
                ({
                    value: kysymys.id.toString(),
                    name: kysymys.title[langKey],
                }) as DropDownItem,
        );

        return [{value: 0, name: t('ei-valintaa')}, ...opts] as DropDownItem[];
    };

    return !show ? (
        <Button
            className="link-alike"
            startIcon={<AddIcon />}
            onClick={toggleShow}
            disabled={disabled}
        >
            {t('lisaa-saanto')}
        </Button>
    ) : (
        <Grid
            container
            direction="column"
            justifyContent="start"
            className={styles['follow-up-box']}
        >
            <p className={styles['select-rules-title']}>
                {t('valitse-kysymyksen-saannot')}
            </p>

            <FormControlLabel
                control={
                    <Checkbox
                        // label="Label"
                        checked={insta === -1}
                        onChange={(event, checked) =>
                            handleFolloupChange(
                                checked,
                                -1,
                                checked ? InputTypes.singletext : null,
                            )
                        }
                        disabled={disabled || dropValue() > 0}
                    />
                }
                label={t('mika-muu-teksti')}
            />

            <FormControlLabel
                control={
                    <Checkbox
                        // label="Label"
                        checked={insta === -2}
                        onChange={(event, checked) =>
                            handleFolloupChange(
                                checked,
                                -2,
                                checked ? InputTypes.numeric : null,
                            )
                        }
                        disabled={disabled || dropValue() > 0}
                    />
                }
                label={t('mika-muu-numero')}
            />

            <DropDownField
                id="followupQ"
                label={t('valitse-kysymys')}
                labelStyles={{fontWeight: 'normal'}}
                onChange={(val) =>
                    parseInt(val, 10) === 0
                        ? handleFolloupChange(false, -1, null)
                        : handleFolloupChange(true, parseInt(val, 10), null)
                }
                value={dropValue().toString()}
                options={followUpOptions()}
                required={false}
                disabled={disabled || insta < 0}
                className={styles['select-rules-dropdown']}
            />
            <div>
                <Button
                    className="link-alike"
                    startIcon={<RemoveIcon className={styles['remove-icon']} />}
                    onClick={toggleShow}
                    disabled={disabled}
                >
                    {t('poista-saanto')}
                </Button>
            </div>
        </Grid>
    );
}

export default FollowupQuestion;
