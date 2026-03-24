import {KyselyCollectionType} from '@cscfi/shared/services/Raportointipalvelu-api/Raportointipalvelu-api-service';
import {ArvoRoles} from '@cscfi/shared/services/Login/Login-service';
import LomakeTyyppi, {paakayttajaLomakkeet} from '@cscfi/shared/utils/LomakeTyypit';
import {useTranslation} from 'react-i18next';
import {useId, useState} from 'react';
import {Collapse} from '@mui/material';
import styles from './Tiedonkeruu.module.css';
import Table from './Table';
import GuardedComponentWrapper from '../../components/GuardedComponentWrapper/GuardedComponentWrapper';
import ButtonWithoutStyles from '../../components/ButtonWithoutStyles/ButtonWithoutStyles';
import AnsweredLessThan50 from './AnsweredLessThan50';

interface KyselyTableProps {
    kysely: KyselyCollectionType;
}

function TiedonkeruuKysely({kysely}: KyselyTableProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['tiedonkeruun-seuranta']);
    const [expanded, setExpanded] = useState<boolean>(false);

    const kyselyWrapperId = `krwap_${useId()}`;
    const answeredLessThanId = `lesst_${useId()}`;

    return (
        <div key={kyselyWrapperId} className={styles['kyselyt-wrapper']}>
            <h3>{lang === 'sv' ? kysely.nimi_sv : kysely.nimi_fi}</h3>
            <Table kysely={kysely} />
            {!paakayttajaLomakkeet.includes(kysely?.lomaketyyppi as LomakeTyyppi) && (
                <GuardedComponentWrapper roles={{arvo: [ArvoRoles.PAAKAYTTAJA]}}>
                    <div className={styles['open-answered-less-than50-wrapper']}>
                        <ButtonWithoutStyles
                            onClick={() => setExpanded(!expanded)}
                            isExpanded={expanded}
                            ariaControls={answeredLessThanId}
                        >
                            <span style={{color: '#2f487f'}}>
                                {t('nayta-toimipaikat')}
                            </span>
                        </ButtonWithoutStyles>
                    </div>
                    <Collapse in={expanded}>
                        <AnsweredLessThan50
                            id={answeredLessThanId}
                            kysely={kysely}
                            handleExpandedChange={() => setExpanded(!expanded)}
                        />
                    </Collapse>
                </GuardedComponentWrapper>
            )}
        </div>
    );
}

export default TiedonkeruuKysely;
