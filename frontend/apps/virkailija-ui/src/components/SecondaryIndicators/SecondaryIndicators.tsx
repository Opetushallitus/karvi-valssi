import React, {useContext, useEffect, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {IconButton} from '@mui/material';
import RenmoveIcon from '@mui/icons-material/Delete';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import {
    IndikaattoriGroupType,
    virkailijapalveluGetProsessitekijaIndikaattorit$,
    virkailijapalveluGetRakennetekijaIndikaattorit$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {SekondaarinenIndikaattoriType} from '@cscfi/shared/services/Data/Data-service';
import LomakeTyyppi, {
    lomakeTyypitKansallisetList,
    lomakeTyypitProsessitekijaList,
} from '@cscfi/shared/utils/LomakeTyypit';
import UserContext from '../../Context';
import styles from './SecondaryIndicators.module.css';

interface MenuProps {
    selectedSecondaryIndicators?: SekondaarinenIndikaattoriType[];
    setSelectedSecondaryIndicators?: React.Dispatch<
        React.SetStateAction<SekondaarinenIndikaattoriType[]>
    >;
    lomaketyyppi: string;
    save?: (e: SekondaarinenIndikaattoriType[]) => void;
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
    const forceUpdate: () => void = React.useState({})[1].bind(null, {}); // Doesn't work without
    const [indikaattoriList, setIndikaattoriList] = useState<
        SekondaarinenIndikaattoriType[]
    >([]);
    const [indikaattori, setIndikaattori] = useState<string>(indikaattoriList[0]?.key);
    const [indikaattoritVisible, setIndikaattoritVisible] = useState<boolean>(false);

    useEffect(() => {
        const editIndicatorList = (tekijaIndikaattorit: Array<IndikaattoriGroupType>) => {
            const newListObj = tekijaIndikaattorit
                .flatMap((indGr) => indGr.indicators)
                .filter((ind) => ind.key !== paaIndikaattori)
                .filter(
                    (ind) =>
                        !selectedSecondaryIndicators?.find(
                            (selected) => selected.key === ind.key,
                        ),
                );
            setIndikaattoriList(newListObj);
        };

        if (lomakeTyypitKansallisetList.includes(lomaketyyppi as LomakeTyyppi)) {
            // combine prosessi- and rakenne-indicators into a single list
            virkailijapalveluGetProsessitekijaIndikaattorit$(userInfo!)().subscribe({
                next: (prosRyhmat: Array<IndikaattoriGroupType>) => {
                    virkailijapalveluGetRakennetekijaIndikaattorit$(
                        userInfo!,
                    )().subscribe({
                        next: (rakRyhmat: Array<IndikaattoriGroupType>) => {
                            editIndicatorList(prosRyhmat.concat(rakRyhmat));
                        },
                    });
                },
            });
        } else if (
            lomakeTyypitProsessitekijaList.includes(lomaketyyppi as LomakeTyyppi)
        ) {
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
        const selectedIndicator = indikaattori || indikaattoriList[0]?.key;
        const found = indikaattoriList.find(
            (obj: SekondaarinenIndikaattoriType) => obj.key === selectedIndicator,
        );
        if (found && selectedSecondaryIndicators) {
            selectedSecondaryIndicators.push(found);
            indikaattoriList.forEach(
                (obj: SekondaarinenIndikaattoriType, index: number) => {
                    if (obj.key === selectedIndicator) {
                        indikaattoriList.splice(index, 1);
                    }
                },
            );
            if (setSelectedSecondaryIndicators) {
                setSelectedSecondaryIndicators(selectedSecondaryIndicators);
            }
            setIndikaattori(indikaattoriList[0].key);
            forceUpdate();
            if (save) {
                save(selectedSecondaryIndicators);
            }
        }
    };
    const DeleteSecondaryIndicator = (index: number) => {
        if (selectedSecondaryIndicators) {
            indikaattoriList.unshift(selectedSecondaryIndicators[index]);
            selectedSecondaryIndicators.splice(index, 1);
            setIndikaattoriList(indikaattoriList);
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
                        {selectedSecondaryIndicators?.map(
                            (item: SekondaarinenIndikaattoriType, i) => (
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
                            ),
                        )}
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
                            {indikaattoriList[0]?.key && (
                                <Select
                                    id="secondaryIndicator"
                                    value={indikaattori || indikaattoriList[0]?.key}
                                    onChange={(e) => {
                                        setIndikaattori(e.target.value);
                                    }}
                                >
                                    {indikaattoriList.map((item) => (
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
