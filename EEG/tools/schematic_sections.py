"""Readable direct wiring and annotations, without changing intended net names."""
def draw_sections(tree, pins, sheet, String, effects, uid):
    handled=set(); counter=0; wires=set(); junctions=set()
    def grid(v):return round(round(v/1.27)*1.27,5)
    def tag(kind):
        nonlocal counter
        counter+=1
        return uid(f'{sheet}-{kind}-{counter}')
    def point(pair):return pins[(pair[0],str(pair[1]))]['xy']
    def wire(a,b):
        a=tuple(round(v,5) for v in a);b=tuple(round(v,5) for v in b)
        if a==b:return
        assert a[0]==b[0] or a[1]==b[1], (sheet,a,b)
        key=tuple(sorted((a,b)))
        if key in wires:return
        wires.add(key)
        tree.append(['wire',['pts',['xy',*a],['xy',*b]],['stroke',['width',0],['type','default']],['uuid',tag('wire')]])
    def path(points):
        for a,b in zip(points,points[1:]):wire(a,b)
    def junction(p):
        if p in junctions:return
        junctions.add(p)
        tree.append(['junction',['at',*p],['diameter',0],['color',0,0,0,0],['uuid',tag('junction')]])
    def label(net,at,angle):
        e=effects()
        if angle in (0,180):e.append(['justify','left' if angle==0 else 'right'])
        tree.append(['global_label',String(net),['shape','bidirectional'],['at',*at,angle],e,['uuid',tag('label')]])
    def group(net,pairs,axis,value,anchor,angle=0,label_anchor=None):
        value=grid(value);anchor=tuple(round(v,5) for v in anchor)
        coords=[anchor]
        for pair in pairs:
            key=pair[0],str(pair[1]);assert pins[key]['net']==net,(key,net,pins[key]['net'])
            handled.add(key);p=point(pair)
            q=(p[0],value) if axis=='y' else (value,p[1])
            wire(p,q);coords.append(q)
        assert all(p[1]==value for p in coords) if axis=='y' else all(p[0]==value for p in coords)
        coords=sorted(set(coords),key=lambda p:p[0] if axis=='y' else p[1])
        for a,b in zip(coords,coords[1:]):wire(a,b)
        for p in coords:junction(p)
        label(net,label_anchor or anchor,angle)
    def title(text,x,y,size=1.8):
        e=['effects',['font',['size',size,size]],['justify','left']]
        tree.append(['text',String(text),['at',x,y,0],e,['uuid',tag('heading')]])

    if sheet=='Inputs':
        title('ELECTRODES / INPUT PROTECTION',25,15,2.54)
        title('J1: channels 1-4, reference, bias',25,24,1.27)
        title('Bias electrode: two independent series resistors',130,20,1.27)
        y=point(('R11',2))[1]
        group('BIAS_LIMIT',[('R11',2),('R12',1)],'y',y,(grid(175),y),270)
        for ch,xa,yp in ((1,50,85),(2,240,85),(3,50,190),(4,240,190)):
            rp=2*ch-1;rn=(9,33,35,37)[ch-1];dn=(5,7,8,9)[ch-1]
            title(f'CHANNEL {ch} / DIFFERENTIAL FILTER',xa-20,yp-23,1.8)
            title('Positive electrode above; shared REF branch below',xa-20,yp-16,1.0)
            y=point((f'R{rp}',2))[1]
            # The clamp's net label sits at its branch endpoint, not in the signal path.
            pairs=[(f'R{rp}',2),(f'R{rp+1}',1),(f'D{ch}',3)]
            labelpoint=point((f'D{ch}',3))
            group(f'CH{ch}_CLAMP',pairs,'y',y,(labelpoint[0],y),180,labelpoint)
            group(f'CH{ch}_ADC',[(f'R{rp+1}',2),(f'C{ch}',1)],'y',y,(grid(xa+135),y),0)
            yn=point((f'R{rn}',2))[1]
            group('REF_CLAMP' if ch==1 else f'REF{ch}_CLAMP',[(f'R{rn}',2),(f'R{rn+1}',1),(f'D{dn}',3)],'y',yn,(point((f'D{dn}',3))[0],yn),180,point((f'D{dn}',3)))
            group(f'CH{ch}_N',[(f'R{rn+1}',2),(f'C{ch}',2)],'y',yn,(grid(xa+135),yn),0)
        title('20 kOhm per input branch / 4.7 nF differential / rail clamps are not a certified patient interface',25,270,1.0)
    elif sheet=='Frontend':
        title('ADS1299-4 / ACQUISITION CORE',25,15,2.54)
        title('Four differential inputs from Inputs sheet; SRB1/SRB2 not used',25,24,1.27)
        title('REFERENCE / VCAP BYPASS',190,45,1.8)
        title('Follow TI placement guidance; C6 polarity matters',190,53,1.0)
        title('Bias amplifier feedback',330,119,1.27)
        for net,pin,x,angle in (('BIAS_OUT',1,335,180),('BIAS_INV',2,365,0)):
            x=grid(x);a=point(('R13',pin));b=point(('C5',pin))
            path([a,(x,a[1]),(x,b[1]),b]);handled.update({('R13',str(pin)),('C5',str(pin))})
            label(net,(x,grid(150)),angle)
        title('Hardware defaults',25,161,1.27)
        title('5 V analog bypass / bulk',25,203,1.27)
        analog=[('C'+str(n),1) for n in (13,14,15,16,17,19,20)]+[('R14',1)]
        group('A5V',analog,'y',215,(grid(30),grid(215)),180)
        group('A5V_CP',[('R14',2),('C18',1)],'y',215,(grid(310),grid(215)),90)
        group('3V3',[('C21',1),('C22',1)],'y',215,(grid(380),grid(215)),90)
        grounds=[('C'+str(n),2) for n in (13,14,15,16,17,18,19,20,21,22)]
        group('GND',grounds,'y',235,(grid(175),grid(235)),270)
        title('AVDD1 feed',275,202,1.0);title('Digital bypass',345,202,1.0)
        title('Unused GPIO pull-downs',25,253,1.27)
    elif sheet=='Power':
        title('BATTERY INPUT / DISCONNECT',25,15,2.54)
        title('2S battery / USB-C via diode OR / no charging',235,35,1.27)
        y=point(('F1',1))[1]
        group('BAT_PLUS',[('J2',1),('F1',1)],'y',y,(grid(65),y),270)
        group('BAT_FUSED',[('F1',2),('D6',2)],'y',y,(grid(108),y),270)
        group('BAT_PROTECTED',[('D6',1),('J4',1)],'y',y,(grid(145),y),270)
        p=point(('J4',2));handled.add(('J4','2'))
        path([p,(grid(165),p[1]),(grid(165),grid(61)),(grid(215),grid(61))]);label('BAT_SW',(grid(215),grid(61)),0)
        title('3.3 V / DIGITAL SUPPLY',25,75,1.8)
        group('BAT_SW',[('C28',1),('C29',1),('U3',3),('U3',2)],'x',120,(grid(120),grid(85)),90)
        group('BUCK_SW',[('U3',5),('C30',2),('L1',1)],'y',90,(grid(175),grid(90)),90)
        y=point(('U3',6))[1]
        group('BUCK_BST',[('U3',6),('C30',1)],'y',y,(grid(195),y),0)
        group('3V3',[('L1',2),('C31',1),('C32',1)],'y',90,(grid(350),grid(90)),0)
        p=point(('U3',1));handled.add(('U3','1'))
        path([p,(grid(165),p[1]),(grid(165),grid(140)),(grid(260),grid(140)),(grid(260),grid(90))]);junction((grid(260),grid(90)))
        group('GND',[('C28',2),('C29',2),('U3',4),('C31',2),('C32',2)],'y',150,(grid(215),grid(150)),270)
        title('5 V / QUIET ANALOG SUPPLY',25,170,1.8)
        group('BOOST9V',[('C33',1),('U4',1),('U4',3)],'x',120,(grid(120),grid(185)),90)
        group('A5V',[('U4',5),('C35',1),('C36',1)],'y',185,(grid(350),grid(185)),0)
        y=point(('U4',4))[1]
        group('LDO_BP',[('U4',4),('C34',1)],'y',y,(grid(195),y),0)
        group('GND',[('C33',2),('U4',2),('C34',2),('C35',2),('C36',2)],'y',235,(grid(215),grid(235)),270)
        title('Power flags / ERC declarations',25,255,1.0)
        title('3V3 POWER INDICATOR / steady DC',285,252,1.0)
        y=point(('R45',2))[1]
        group('PWR_LED_A',[('R45',2),('D13',2)],'y',y,(grid(330),y),270)
        title('[P5] R45 = 1 kOhm; LED indicates 3V3 only, not analog readiness.',235,275,1.0)
        title('J4 shunt enables power; remove shunt or unplug battery for storage',235,55,1.0)
    elif sheet=='Controller':
        title('EXTERNAL ESP32 / CABLE INTERFACE',25,15,2.54)
        title('J5 is a signal cable header, not a plug-in dev-board socket',25,24,1.27)
        title('SPI series damping / 3.3 V logic',110,45,1.27)
        title('Local interface bypass',235,45,1.27)
        title('Automatic external-board power / disconnect power wire before its USB',190,110,1.0)
        title('Selected input voltage monitor / ratio 4.3',225,150,1.27)
        group('3V3',[('C24',1),('C25',1)],'y',60,(grid(275),grid(60)),90)
        group('GND',[('C24',2),('C25',2)],'y',85,(grid(275),grid(85)),270)
        y=point(('R31',2))[1]
        group('VIN_SENSE',[('R31',2),('R32',1),('C27',1)],'y',y,(grid(285),y),90)
    elif sheet=='USB':
        title('USB-C BENCH INPUT / ANALOG BOOST',25,15,2.54)
        title('5 V supply only; no USB data, PD, or battery charging',25,24,1.27)
        title('Independent CC pull-downs',105,45,1.27)
        title('F2 + D10 feed shared protected input',180,45,1.27)
        title('LOW-CURRENT ANALOG BOOST / 9.04 V NOMINAL',155,120,1.8)
        group('BOOST_SW',[('U5',1),('L2',2),('D11',2)],'x',250,(grid(250),grid(140)),90)
        group('BOOST9V',[('U5',5),('D11',1),('C38',1),('R41',1)],'x',300,(grid(300),grid(140)),90)
        group('BOOST_FB',[('U5',3),('R41',2),('R42',1)],'y',205,(grid(250),grid(205)),270)
        title('USB presence monitor / separate from selected supply voltage',25,185,1.0)
        group('USB_PRESENT',[('R43',2),('R44',1),('C40',1)],'y',210,(grid(95),grid(210)),90)
    # Educational annotations are plain text: never electrical labels or wires.
    # Coordinates deliberately use whitespace between circuit groups.
    def note(x, y, lines):
        for i, line in enumerate(lines):
            title(line, x, y + i * 3.5, 1.15)

    if sheet == 'Inputs':
        note(240, 24, [
            '[I0] REF compares all channels; BIAS is a driven output.',
            'J1 has no circuit-ground electrode. Trace CH1_E to CH1_ADC.',
            'BIAS current path: R11 + R12 = 998 kOhm; bench validation pending.',
        ])
        note(30, 145, [
            '[I1] R1/R9 limit current toward the clamps; R2/R10 add isolation.',
            'D1/D5: low-leakage rail clamps; leakage creates input offset.',
            'C1 bridges P/N: 40 kOhm differential + 4.7 nF gives about 847 Hz.',
            'This is high-frequency attenuation, not the final EEG bandpass.',
        ])
        note(220, 145, [
            '[I2] REF_E fans out into four separate protected branches.',
            'Each channel has its own negative input and differential capacitor.',
            'A disturbance on the shared reference can affect several channels.',
            'Channels 3/4 repeat this topology. Clamps do not certify safety.',
        ])
    elif sheet == 'Frontend':
        note(25, 36, [
            '[F1] U1 converts four differential channels simultaneously.',
            '24-bit format does not imply 24-bit measurement accuracy.',
        ])
        note(185, 98, [
            '[F2] VCAP capacitors support internal circuits; not spare supplies.',
            'C11/C12 steady the ADC conversion reference, not the REF electrode.',
            'Use specified values and short local return paths; C6 is polarized.',
        ])
        note(320, 168, [
            '[F3] R13 || C5 shapes bias feedback.',
            'RC scale ~159 Hz; actual loop stability needs testing.',
            'Use internal bias reference; enable after bench checks.',
        ])
        note(235, 184, [
            '[F4] Pulls define startup: RESET/START low, CS high.',
            'CLKSEL/PWDN high; firmware must configure the ADC.',
        ])
        note(25, 282, [
            '[F5] Local bypass supplies transient current. R14 is a removable link, not a filter.',
        ])
    elif sheet == 'Power':
        note(235, 18, [
            '[P1] F1: thermal overcurrent response, not a precise cutoff.',
            'D6/D10 diode OR inputs; battery normally wins when both connected.',
            'J4 disconnects BAT_SW; unplug the pack for master isolation.',
        ])
        note(180, 115, [
            '[P2] U3 + L1 transfer switched energy to 3V3.',
            'C30: bootstrap. C31/C32: output charge.',
            'FB senses 3V3; measure switching ripple.',
        ])
        note(25, 162, [
            '[P3] Separate analog LDO avoids another local switch node; it is not galvanic isolation.',
        ])
        note(235, 242, [
            'C34 bypasses the LDO noise-related node; C35 supports stability.',
            'Check effective capacitance / ESR for the installed LP2985 revision.',
            'Boost gives analog headroom from USB; LDO loss ~ (9.04-5) V x I.',
        ])
        note(25, 282, [
            '[P4] PWR_FLAG declares a driven rail for ERC; it adds no physical part.',
            'The pack needs independent protection. No onboard charger or hardware low-voltage cutoff.',
        ])
    elif sheet == 'Controller':
        note(25, 140, [
            '[C1] J5 exposes SPI, DRDY, RESET, START, sense signals and ground.',
            'Use short cables and 3.3 V GPIO. No onboard ESP32 or RF circuit.',
            'Suggested S3 GPIO map is in README; verify the actual dev board.',
        ])
        note(25, 180, [
            '[C2] Wi-Fi target: HTTP UI + WebSocket frames; firmware pending.',
            'Read on DRDY; use a bounded buffer so networking cannot block sampling.',
            'Program through the external board USB, with electrodes disconnected.',
        ])
        note(25, 220, [
            '[C3] J5 pin 2 is permanently supplied by the EEG 3.3 V rail.',
            'Disconnect the J5 pin 2 power cable before its own USB.',
            'Do not feed a dev-board 5 V pin from this 3.3 V output.',
            'VIN_SENSE measures BAT_SW; USB_PRESENT identifies USB bench power.',
        ])
        note(225, 245, [
            '[C4] R31/R32 ratio: 4.3. Verify ADC calibration and settling.',
            'USB mode must not use the 6.4 V battery-mode cutoff threshold.',
        ])
    elif sheet == 'USB':
        note(25, 155, [
            '[U1] CC1/CC2 each need their own 5.1 kOhm sink resistor.',
            'Use a 5 V bench adapter rated >=1 A; no PD negotiation.',
            'No USB data is connected. Use the dev-board USB for programming.',
        ])
        note(165, 250, [
            '[U2] Vout = 0.2 V x (1 + 442k / 10k) = 9.04 V nominal.',
            'U5 boosts BAT_SW only for the analog LDO; ESP32 uses the 3.3 V buck.',
            'D6/D10 diode OR blocks backfeed; connecting USB still connects grounds.',
            'Bench-only USB: disconnect electrodes before any wired connection.',
        ])
        note(25, 282, [
            '[U3] USB_PRESENT = VBUS / 4.3; analog presence indication, not USB negotiation.',
        ])

    # KiCad expects junctions at wire endpoints. Split long buses at every tap
    # before export so parser repair cannot discard a bus fragment.
    existing=[n for n in tree if isinstance(n,list) and n and n[0]=='wire']
    for n in existing:tree.remove(n)
    emitted=set()
    for n in existing:
        pts=next(c for c in n if isinstance(c,list) and c[0]=='pts')
        a,b=(tuple(float(v) for v in p[1:]) for p in pts[1:])
        vertical=a[0]==b[0]
        axis=1 if vertical else 0
        cuts={a,b}
        for p in junctions:
            if p[1-axis]==a[1-axis] and min(a[axis],b[axis])<p[axis]<max(a[axis],b[axis]):cuts.add(p)
        cuts=sorted(cuts,key=lambda p:p[axis])
        for p,q in zip(cuts,cuts[1:]):
            key=tuple(sorted((p,q)))
            if key in emitted:continue
            emitted.add(key)
            tree.append(['wire',['pts',['xy',*p],['xy',*q]],['stroke',['width',0],['type','default']],['uuid',tag('split-wire')]])
    return handled
