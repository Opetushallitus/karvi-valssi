import React, {useContext, useEffect, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {IconButton} from '@mui/material';
import RenmoveIcon from '@mui/icons-material/Delete';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import {
    IndikaattoriGroupType,
    IndikaattoriType,
    virkailijapalveluGetProsessitekijaIndikaattorit$,
    virkailijapalveluGetRakennetekijaIndikaattorit$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import UserContext from '../../Context';
import styles from './SecondaryIndicators.module.css';

interface MenuProps {
    selectedSecondaryIndicators?: IndikaattoriType[];
    setSelectedSecondaryIndicators?: React.Dispatch<
        React.SetStateAction<IndikaattoriType[]>
    >;
    lomaketyyppi: string;
    save?: (e: IndikaattoriType[]) => void;
    paaIndikaattori: string;
}
function SecondaryIndicatorsComponent({
    selectedSecondaryIndicators,
    setSelectedSecondaryIndicators,
    lomaketyyppi,
    save,
    paaIndikaattori,
}: MenuProps) {
    const {t} = useTranslation(['sekondaariset-indikaattorit']);
    const userInfo = useContext(UserContext);
    const forceUpdate: () => void = React.useState({})[1].bind(null, {}); // Doesnt work without
    const [indicaattoriList, setIndicaattoriList] = useState<IndikaattoriType[]>([]);
    const [indikaattori, setIndikaattori] = useState<string>(indicaattoriList[0]?.key);
    const [indikaattoritVisible, setIndikaattoritVisible] = useState<boolean>(false);

    useEffect(() => {
        const editIndicatorList = (tekijaIndikaattorit: Array<IndikaattoriGroupType>) => {
            let listObj: IndikaattoriType[] = [];
            tekijaIndikaattorit.forEach((obj: IndikaattoriGroupType) =>
                obj.indicators.forEach((childObj: IndikaattoriType) => {
                    if (paaIndikaattori !== childObj.key) {
                        listObj.push(childObj);
                    }
                }),
            );
            listObj = listObj.filter(
                (ar: IndikaattoriType) =>
                    !selectedSecondaryIndicators?.find((rm) => rm.key === ar.key),
            );
            setIndicaattoriList(listObj);
        };
        if (lomaketyyppi === 'prosessitekijat') {
            virkailijapalveluGetProsessitekijaIndikaattorit$(userInfo!)().subscribe({
                next: (ryhmat: Array<IndikaattoriGroupType>) => {
                    editIndicatorList(ryhmat);
                },
            });
        } else {
            virkailijapalveluGetRakennetekijaIndikaattorit$(userInfo!)().subscribe({
                next: (ryhmat: Array<IndikaattoriGroupType>) => {
                    editIndicatorList(ryhmat);
                },
            });
        }
    }, [lomaketyyppi, paaIndikaattori, selectedSecondaryIndicators, userInfo]);

    const addSecondaryIndicator = () => {
        const selectedIndicator = indikaattori || indicaattoriList[0]?.key;
        const found = indicaattoriList.find(
            (obj: IndikaattoriType) => obj.key === selectedIndicator,
        );
        if (found && selectedSecondaryIndicators) {
            selectedSecondaryIndicators.push(found);
            indicaattoriList.forEach((obj: IndikaattoriType, index: number) => {
                if (obj.key === selectedIndicator) {
                    indicaattoriList.splice(index, 1);
                }
            });
            if (setSelectedSecondaryIndicators) {
                setSelectedSecondaryIndicators(selectedSecondaryIndicators);
            }
            setIndikaattori(indicaattoriList[0].key);
            forceUpdate();
            if (save) {
                save(selectedSecondaryIndicators);
            }
        }
    };
    const DeleteSecondaryIndicator = (index: number) => {
        if (selectedSecondaryIndicators) {
            indicaattoriList.unshift(selectedSecondaryIndicators[index]);
            selectedSecondaryIndicators.splice(index, 1);
            setIndicaattoriList(indicaattoriList);
            if (setSelectedSecondaryIndicators) {
                setSelectedSecondaryIndicators(selectedSecondaryIndicators);
            }
            forceUpdate();
            if (save) {
                save(selectedSecondaryIndicators);
            }
        }
    };
    return (
        <div>
            {selectedSecondaryIndicators && selectedSecondaryIndicators[0] && (
                <div>
                    <h2 className={styles.secondHeading}>
                        {t('lomakkeeseen-liittyvät-muut-indikaattorit')}
                    </h2>
                    <ul className={styles.indicatorsList}>
                        {selectedSecondaryIndicators?.map((item: IndikaattoriType, i) => (
                            <div
                                className={styles.indicatorWrapper}
                                key={`item_${item.key}`}
                            >
                                <p>
                                    {t(`desc_${item.key}`, {ns: 'indik'})}
                                    <IconButton
                                        onClick={() => {
                                            DeleteSecondaryIndicator(i);
                                        }}
                                        aria-label={t(
                                            'poista-sekondaarinen-indikaattori',
                                        )}
                                        className="icon-button"
                                    >
                                        <RenmoveIcon />
                                    </IconButton>
                                </p>
                            </div>
                        ))}
                    </ul>
                </div>
            )}
            {!indikaattoritVisible &&
                selectedSecondaryIndicators &&
                selectedSecondaryIndicators.length < 2 && (
                    <button
                        type="button"
                        onClick={() => setIndikaattoritVisible(!indikaattoritVisible)}
                        className={styles.showIndicatorsButton}
                    >
                        {`+ ${t('lisaa-indikaattoreita')}`}
                    </button>
                )}

            {indikaattoritVisible && (
                <div>
                    <div>
                        <label
                            htmlFor="secondaryIndicator"
                            className="label-for-inputfield"
                        >
                            {t('valitse-indikaattorit')}
                        </label>
                        <div className={styles.addWrapper}>
                            {indicaattoriList[0]?.key && (
                                <Select
                                    id="secondaryIndicator"
                                    value={indikaattori || indicaattoriList[0]?.key}
                                    onChange={(e) => {
                                        setIndikaattori(e.target.value);
                                    }}
                                >
                                    {indicaattoriList.map((item: IndikaattoriType) => (
                                        <MenuItem value={item.key} key={item.key}>
                                            {t(item.key, {ns: 'indik'})}
                                        </MenuItem>
                                    ))}
                                </Select>
                            )}
                            <button
                                className="small"
                                type="button"
                                disabled={
                                    !(
                                        selectedSecondaryIndicators &&
                                        selectedSecondaryIndicators.length < 2
                                    )
                                }
                                onClick={() => {
                                    addSecondaryIndicator();
                                }}
                                style={{marginLeft: '0.5rem'}}
                            >
                                {t('tallenna')}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
export default SecondaryIndicatorsComponent;
