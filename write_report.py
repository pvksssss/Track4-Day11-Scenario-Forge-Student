"""Render the report tables directly from the full-budget evidence files."""
from pathlib import Path
import json
import math

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / "evidence" / f"{name}.json").read_text(encoding="utf-8"))


def sci(x):
    return f"{x:.6g}"


def main():
    meta, replay, mc, hunt, est, fix, mine = [load(n) for n in ("meta", "replay", "mc", "hunt", "estimate", "fix", "mine")]
    for data in (meta, replay, mc, hunt, est, fix, mine):
        assert data["_run"]["mssv"] == "2A202602590" and not data["_run"]["quick"]
    chosen, ct, bt = fix["chosen"], fix["chosen_test"], fix["baseline_test"]
    modes = ("bus_bypass", "cut_in", "crosswalk_block", "rear_ended")
    lines = ["MSSV: 2A202602590", "", "# Lab 11 · Scenario Forge — Phạm Văn Kiên", "",
             "Thị trấn: **B** (`meta.json: _run.town`). Toàn bộ evidence dùng ngân sách đầy đủ (`quick=false`), không đổi lõi mô phỏng, phân phối, seed hoặc các policy ứng viên gốc.", "",
             "MSSV có chữ A: chạy bằng `python run_lab.py all`, hoặc đặt `LAB11_MSSV=2A202602590` rồi chạy `run_all.py all`. Giữ nguyên chuỗi MSSV khi hash. Seed trong `meta.json: seeds`: " + json.dumps(meta["seeds"]) + ". Các bảng dưới đọc trực tiếp từ JSON bằng `write_report.py`.", "",
             "## 1. Phát lại log có trung thực không?", "",
             f"`replay.json`: n={replay['n']}; bỏ {replay['dropped_human_crash_logs']} log có người lái thất bại; còn {replay['n_used']} kịch bản. Replay có {replay['replay']['crashes']} va chạm ({replay['replay']['contact'].get('rear',0)} rear, {replay['replay']['contact'].get('side',0)} side, {replay['replay']['contact'].get('front',0)} front); reactive có {replay['reactive']['crashes']}; crash_in_both={replay['crash_in_both']}.", "",
             "Xe sau trong log tiếp tục quỹ đạo đã ghi, không biết planner mới phanh sớm hơn người lái. Nó đâm vào ego trong đánh giá phản thực, dù nếu thực sự có mặt nó có thể phanh theo IDM. Vì vậy các va chạm replay-only không phải bằng chứng planner chắc chắn gây tai nạn trong thế giới phản ứng.", "",
             f"Ví dụ `replay.json: replay_only[0]`, scenario={replay['replay_only'][0]['scenario']}, contact={replay['replay_only'][0]['contact']}, TTC nhỏ nhất trong reactive={sci(replay['replay_only'][0]['min_ttc_reactive'])} s. TG chạy theo log người lái và tông đuôi ego đã giảm tốc. Reactive phản ứng lại nên tránh được. Có thể xem bằng nút R-01 trong viewer.", "",
             "## 2. Kịch bản bất khả thi", "",
             "`lab11/feasible.py: is_feasible` loại nếu: (1) gia tốc ngang `(π/cutDur)²×3.5/2 > μg`; (2) phanh sau nhập làn `cutBrake > μg`; (3) người đi bộ `pedV > 2.5 m/s`; (4) `cutV` ngoài `(0,22] m/s`. Thời gian đổi làn không dương cũng bị loại. Hai luật đầu dựa trên giới hạn bám đường, hai luật sau giới hạn nhóm tác nhân và vận tốc mà bài lab cho phép.", "",
             "| Cuộc săn (`hunt.json`) | Kịch bản bất khả thi | Thất bại tìm được theo nhãn |", "|---|---:|---|"]
    for m in modes:
        lines.append(f"| {m} | {hunt[m]['infeasible']} | {json.dumps(hunt[m]['found'], ensure_ascii=False)} |")
    worst = max(modes, key=lambda m: hunt[m]["infeasible"])
    lines += ["", f"Cuộc săn {worst} loại nhiều nhất: {hunt[worst]['infeasible']}. Các biến làm giảm khoảng phanh hoặc thời gian đổi làn có thể tăng điểm nguy hiểm, kéo CEM về rìa khả thi. Không suy ra luật nào chiếm đa số chỉ từ tổng này. Pipeline bỏ mẫu bất khả thi trước mô phỏng và trước cập nhật elite; nếu đếm chúng là thất bại thì sẽ thổi phồng rủi ro bằng các chuyển động không xảy ra được. `mc.json: infeasible`={mc['infeasible']}.", "",
              "## 3. Monte Carlo cho biết gì?", "",
              f"`mc.json`: k={mc['crashes']}, n={mc['n']}, p̂={sci(mc['p'])}; Wilson 95%=[{sci(mc['lo'])}, {sci(mc['hi'])}]. Chỉ gặp bus_bypass. Để sai số khoảng ±20% của p, gần đúng n≈1.96²(1−p)/(0.2²p)={math.ceil(1.96**2*(1-mc['p'])/(0.2**2*mc['p'])):,} (quy tắc 96/p≈{96/mc['p']:,.0f}). Đây là dự toán dùng p̂ rất bất định từ đúng một lần thất bại.", "",
              f"cut_in, crosswalk_block, rear_ended và other chưa xuất hiện. Với mỗi kiểu, báo cận Wilson trên {sci(mc['per_mode']['cut_in']['hi'])} (`mc.json: per_mode.<mode>.hi`), không kết luận xác suất bằng 0. Chặn lối P1 cũng được tính là thất bại dù chưa có tiếp xúc hình học.", "",
              "## 4. Importance sampling, ESS và suy biến", "",
              "`estimate.json: seeds[s].per[m]` (600 mẫu/kiểu/seed). Ô không hit báo cận `upper_zero_hits`; giá trị p thô trong JSON bằng 0 chỉ là kết quả đếm, không được diễn giải là xác suất thực bằng 0.", "",
              "| Seed | Kiểu | p̂ hoặc cận trên khi chưa thấy | hits | ESS | top_share |", "|---:|---|---:|---:|---:|---:|"]
    for seed in est["seeds"]:
        for m in modes:
            e = seed["per"][m]
            p = sci(e["p"]) if e["hits"] else f"≤ {sci(e['upper_zero_hits'])}"
            lines.append(f"| {seed['seed']} | {m} | {p} | {e['hits']} | {e['ess']:.2f} | {e['top_share']:.4f} |")
    totals = [s["total"] for s in est["seeds"]]
    lines += ["", "Tổng điểm ước lượng của ba seed (`estimate.json: seeds[].total`): " + ", ".join(sci(x) for x in totals) + f"; chênh lớn nhất/nhỏ nhất={max(totals)/min(totals):.2f} lần. Bus_bypass ở seed 0 và 2 cao hơn MC nhưng vẫn trong khoảng Wilson rất rộng của MC; seed 1 thấp hơn nhiều. Không đủ căn cứ kết luận ba seed đã hội tụ.", "",
              "top_share >0.5 ở bus_bypass cả ba seed và crosswalk_block seed 2: hơn nửa kết quả đến từ đúng một mẫu. ESS đo sự lệch trọng số toàn bộ mẫu, không chứng minh đã phủ đủ mọi vùng thất bại; top_share nhỏ cũng không chứng minh hội tụ. Crosswalk_block chênh hơn một bậc giữa seed 0 và 2 dù có nhiều hit, vì các hit có trọng số rất khác nhau.", "",
              f"Ngân sách `estimate.json: budget`={est['budget']:,}, gồm 4×8×300 mẫu săn và 4×3×600 mẫu IS, chưa cộng {mc['n']:,} MC để lấy other. Theo các p̂ bus_bypass, MC muốn ±20% cần khoảng " + ", ".join(f"{96/s['per']['bus_bypass']['p']:,.0f}" for s in est["seeds"]) + " mẫu. Tuy nhiên IS ở đây chưa đạt ±20%: khoảng ±1.96se/p̂ của bus_bypass lần lượt " + ", ".join(f"{1.96*s['per']['bus_bypass']['se']/s['per']['bus_bypass']['p']:.2f}" for s in est["seeds"]) + "; không thể gọi tỷ lệ ngân sách này là mức tăng tốc ở cùng độ chính xác.", "",
              f"`estimate.json: other` lấy từ MC: k={est['other']['k']}, n={est['other']['n']}, hi={sci(est['other']['hi'])}. Nhãn other là tập dư không có điểm săn riêng, nên dùng MC để không bỏ sót nó. Với 0 hit trong IS: q≥0.2p ⇒ cận 95% xấp xỉ 3/(0.2×600)=0.025, không dùng 3/ESS. `seeds[].hi` là khoảng xấp xỉ do pipeline xuất; các kiểu không hit vẫn cần báo cận riêng, không dùng riêng tổng này để chứng nhận an toàn.", "",
              "## 5. Các kiểu thất bại và ảnh 3D", "",
              "**Bus bypass:** C2 chờ khe rồi lách xe buýt đỗ; khi C2 xâm lấn làn ở tốc độ thấp, ngưỡng ngang của ego nhận nó là xe dẫn quá muộn. Ego va vào C2 trước x=112 m với C2 dưới 6 m/s. Ảnh chụp tại sự kiện của B-01, tham số đầy đủ trong `viewer.json: runs` và thời điểm trong `review-scenes.json`.", "",
              "![B-01: lách qua xe buýt tại va chạm](evidence/shots/bus-bypass.jpg)", "",
              "**Crosswalk block:** xe buýt che P1. Người không ngó qua xe buýt chờ theo phần đường nhìn được rồi bước ra. Ego phanh nhưng thân xe dừng trên vạch x=122, chắn đường P1; P1 dừng lại chứ không bước xuyên thân xe. Đây là sự kiện kind=block, không đồng nhất với contact.", "",
              "![C-01: thân xe chắn P1 tại vạch qua đường](evidence/shots/crosswalk-block.jpg)", "",
              "Không tìm được đúng nhãn cut_in và rear_ended trong các cuộc săn của chúng. Điều đó chỉ giới hạn kết quả ở 8 vòng×300 mẫu, không chứng minh chúng không thể xảy ra. `hunt.json: cut_in.found` và `rear_ended.found` còn chứa bus_bypass/crosswalk_block: một cuộc săn chung dễ lặp lại một cơ chế dễ tìm, nên cần tách điểm nguy hiểm theo kiểu và kiểm tra nhãn thực tế.", "",
              "## 6. Sửa planner: TRAIN và TEST", "",
              "Policy chọn từ TRAIN (`fix.json: chosen.policy`): `" + json.dumps(chosen["policy"], ensure_ascii=False) + "`. Xếp theo fail_hi nhỏ nhất trong các ứng viên giữ ≥95% progress baseline; không xếp lại theo TEST.", "",
              "| Nguồn trong fix.json | fail | fail_hi_seen | fail_hi | progress (m) | harsh (khung hình/lần chạy) | unseen |", "|---|---:|---:|---:|---:|---:|---|"]
    for name in ("baseline_train", "chosen", "baseline_test", "chosen_test"):
        r = fix[name]
        lines.append(f"| {name} | {sci(r['fail'])} | {sci(r['fail_hi_seen'])} | {sci(r['fail_hi'])} | {r['progress']:.4f} | {r['harsh']:.4f} | {', '.join(r['unseen']) or '—'} |")
    loss = 1 - ct["progress"] / bt["progress"]
    lines += ["", f"Trên TEST, thay đổi quãng đường={-100*loss:.3f}% so baseline; quãng đường được cắt tại sự kiện thất bại đầu tiên. `harsh` là số khung hình có a<−3 m/s² trung bình, không phải số đợt phanh độc lập. Baseline TRAIN có {fix['baseline_train']['progress']:.4f} m, nên ngưỡng chọn là {0.95*fix['baseline_train']['progress']:.4f} m.", "",
              "TEST dùng seed mới, săn lại dưới policy đã chọn và 3.000 mẫu tự nhiên mới để bắt các kiểu khác. Một kiểu biến mất trong mẫu vẫn mang cận 3/(0.2×400)=0.0375 vào fail_hi. Vì vậy fail_hi có thể lớn hơn fail baseline dù nhiều tình huống cụ thể được cứu; không được thay fail_hi bằng fail_hi_seen để tuyên bố đạt chứng nhận. Các khoảng IS vẫn là xấp xỉ hữu hạn mẫu, đặc biệt khi top_share cao.", "",
              "![FIX: xe chính dùng policy chọn, bóng mờ là baseline trên cùng cảnh](evidence/shots/policy-fix.jpg)", "",
              "Ảnh FIX dùng cảnh B-01 hoặc cảnh thất bại đầu tiên được cứu; nút FIX-* trong `review.html` đặt xe chính là policy đã chọn, bóng mờ là baseline. Bóng mờ thể hiện quỹ đạo baseline va chạm còn xe chính tránh được. Các nút B-*/C-* gốc của exporter ghim baseline làm xe chính, nên không dùng nhãn readout của chúng để đảo kết luận về policy.", "",
              "Ví dụ núm nghe an toàn nhưng có thể phản tác dụng: tăng T kéo giãn khoảng cách ego, tạo khe để C2 đổi làn; thế giới phản ứng nên rủi ro không đơn điệu. Tương tự hạ cautionV nhiều có thể giảm tiến độ và đổi thời điểm gặp P1/C2. Bảng TRAIN dưới đây là đo thực tế trên cùng tập mẫu; không dùng các số này để thay thế TEST.", "",
              "| Policy ứng viên | TRAIN fail | TRAIN fail_hi | progress (m) |", "|---|---:|---:|---:|"]
    for r in fix["table"]:
        lines.append(f"| `{json.dumps(r['policy'])}` | {sci(r['fail'])} | {sci(r['fail_hi'])} | {r['progress']:.3f} |")
    lines += ["", "## 7. Từ mô phỏng ra đường thật", "",
              "| Giả định | Dữ liệu cần và nguồn cụ thể | Hướng sai lệch nếu giả định quá lạc quan |", "|---|---|---|",
              "| Khe chấp nhận của C2, lognormal median 12 m ở B | Quỹ đạo camera trên cao tại đoạn có xe buýt đỗ, đo khe trước/sau lúc bắt đầu nhập làn; dùng INTERACTION/inD để đối chiếu hành vi nhưng cần thu riêng bối cảnh xe buýt | Nếu khe thực nhỏ hơn, nhiều lần nhập sát đầu ego hơn, ước lượng bus_bypass có thể bị thấp; tương tác thời điểm có thể làm quan hệ không đơn điệu |",
              "| 85% người đi bộ ngó qua xe buýt | Video đồng bộ từ camera vỉa hè và xe, gán nhãn hướng đầu, phần đường nhìn được, thời điểm bước ra; bổ sung quan sát thực địa có xe buýt đỗ vì quỹ đạo đơn thuần không xác định được động tác ngó | Nếu ít người ngó hơn mô hình, tăng tình huống P1 bước ra khi ego bị che, có thể tăng crosswalk_block |",
              "| 30% đường ướt; μ=0.5 ướt và 0.8 khô | Nhật ký mưa trên đúng tuyến kết hợp đo ma sát bằng xe đo hoặc thử phanh có kiểm soát theo loại lốp, mặt đường và tốc độ | Nếu μ thực thấp hơn hay đường ướt nhiều hơn, khoảng phanh thực dài hơn và rủi ro phanh muộn có thể bị đánh giá thấp |", "",
              "Không lấy tần suất hiếm ở mô phỏng làm số liệu giao thông thực. Cần hiệu chỉnh phân phối chung và các tương quan (mưa, tầm nhìn, hành vi), không chỉ thay từng trung bình độc lập.", "",
              "## 8. Giới hạn", "",
              "1. Chỉ một đoạn phố và 24 s: xác suất theo một lần mô phỏng không đại diện mọi tuyến hoặc mọi độ dài chuyến đi.",
              "2. Xe khác chủ yếu IDM, đổi làn bằng chấp nhận khe, hành vi người đi bộ được lập trình: không có toàn bộ độ trễ, mất chú ý hoặc kiểu lái ngoài đời.",
              "3. Cảm biến trong lõi gần lý tưởng ngoài che khuất, không có đầy đủ sai số phát hiện/định vị và thời gian suy luận thực; sai lệch sim-to-real không được bao trong Wilson CI.", "",
              "Nếu có thêm một tuần: thu video khe nhập làn và hành vi P1 quanh xe buýt; thêm trễ cảm biến/phanh; chia lại holdout theo cảnh và thời tiết; tăng ngân sách cho các kiểu không hit và kiểm tra độ phủ proposal qua nhiều seed trước khi báo mức rủi ro nhỏ.", "",
              "## 9. Rắc rối riêng: xe đạp lạng vào làn trước giao lộ", "",
              "Xe đạp H0 chạy ở mép trái E2, lạng 2 m vào E1 khi ego còn cách 9 m. Cảnh chính xác bắt đầu ở x=0, v=3 m/s, d=−1.2 m, swDur=1.9 s. Tương tự người đi xe đạp né chướng ngại trên mép đường rồi đi vào đường xe phía sau. Planner đợi đủ xâm lấn ngang mới nhận là vật cản dẫn đường, nên có nguy cơ phanh muộn. `mine.json: exact.planner`=" + json.dumps(mine["exact"]["planner"], ensure_ascii=False) + ".", "",
              "`hazard.json: space`: x∼U[−5,10] m; v∼U[2,4] m/s; khoảng cách kích hoạt∼U[7,13] m; swDur∼U[1.9,2.2] s. Đây là dải thiết kế có chủ đích để thử xâm lấn ngang trước giao lộ x=80, không phải mẫu đã fit từ video. Gia tốc ngang π²×2/(2swDur²)=2.04–2.73 m/s², dưới 3; tốc độ tương đương 7.2–14.4 km/h. Mọi điều kiện khác lấy theo thị trấn B (`mine.json: conditional_on`).", "",
              f"Quét chính thức 1.500 mẫu: accepted={mine['accepted']:.6f}, infeasible={mine['infeasible']} (`mine.json`).", "",
              "| mine.json | n sau lọc chồng lấn | Tổng va chạm | avoidable | unavoidable | unattributed | low_speed | avoidable_foreknown |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name in ("baseline", "chosen"):
        r = mine[name]
        lines.append(f"| {name} | {r['n']} | {r['crashes']} | {r['avoidable']} | {r['unavoidable']} | {r['unattributed']} | {r['low_speed']} | {r['avoidable_foreknown']} |")
    lines += ["", "| Policy | P(lỗi planner ∣ hazard) | Wilson 95% | Tần suất/chuyến với exposure giả định 0.002 | Cận trên/chuyến |", "|---|---:|---|---:|---:|"]
    for name in ("baseline", "chosen"):
        r = mine[name]
        p_text = sci(r['p']) if r['avoidable'] else f"≤ {sci(r['hi'])} (0/{r['n']} hit)"
        trip_text = sci(r['per_trip']) if r['avoidable'] else f"≤ {sci(r['per_trip_hi'])}"
        lines.append(f"| {name} | {p_text} | [{sci(r['lo'])}, {sci(r['hi'])}] | {trip_text} | {sci(r['per_trip_hi'])} |")
    lines += ["", "Chỉ avoidable là tử số lỗi planner: phanh tối đa từ khung đầu hazard đã hoạt động và cảm biến nhìn thấy thì tránh được mọi va chạm ego. unavoidable vẫn va chạm khi phanh như vậy. unattributed là va chạm đầu tiên với tác nhân không quy cho hazard; không nhất thiết chỉ do hazard chưa bắt đầu. low_speed là cờ chồng lên các loại, khi ego<1 m/s, không phải loại thứ tư. Kiểm tra tổng ba loại bằng crashes.", "",
              "Oracle phản ứng ngay khi nhìn thấy và phanh tối đa nên lạc quan hơn planner thực có độ trễ; theo hướng này avoidable có thể đếm nhiều hơn số tai nạn thực tế có thể cứu. Ngược lại, chỉ thử phanh, không thử đánh lái, có thể bỏ sót những vụ tránh được bằng điều khiển khác. Khoảng cách avoidable_foreknown−avoidable phản ánh phần thiệt hại vì che khuất trong phép thử này.", "",
              "Exposure không có dữ liệu thực để hiệu chỉnh: giả định vận hành minh họa P(gặp xe đạp gần làn)=0.1/chuyến × P(lạng∣gặp)=0.02, bằng 0.002/chuyến (`hazard.json: why`). Hai số là giả định được công khai, không phải thống kê đã quan sát; không dùng để tuyên bố rủi ro ngoài đời. Bảng độ nhạy:", "",
              "| Exposure giả định/chuyến | Baseline/chuyến | Policy chọn/chuyến |", "|---:|---:|---:|"]
    for ex in (0.0002, 0.002, 0.02):
        chosen_freq = sci(ex*mine['chosen']['p']) if mine['chosen']['avoidable'] else '≤ ' + sci(ex*mine['chosen']['hi'])
        lines.append(f"| {ex} | {sci(ex*mine['baseline']['p'])} | {chosen_freq} |")
    bus = sorted(s["per"]["bus_bypass"]["p"] for s in est["seeds"])[1]
    chosen_trip = sci(mine['chosen']['per_trip']) if mine['chosen']['avoidable'] else 'cận trên ' + sci(mine['chosen']['per_trip_hi'])
    lines += ["", f"Đặt cạnh bus_bypass: trung vị ba seed IS={sci(bus)} trên một lần chạy tự nhiên 24 s. Tần suất xe đạp có exposure là {sci(mine['baseline']['per_trip'])} baseline và {chosen_trip} policy chọn. Chỉ so được trong quy ước một chuyến tương ứng một đoạn 24 s và exposure đã nêu; mẫu số và độ bất định không đủ để xếp hạng rủi ro ngoài đời.", "",
              "![Xe đạp H0: cảnh chính xác tại va chạm 4.65 s](evidence/shots/hazard-bike.jpg)", "",
              f"Bản sửa từ E dùng cutinLat=3.0, nhận tác nhân đang lấn ngang làm xe dẫn sớm hơn. Nó cũng xử lý tốt hazard xe đạp: {mine['chosen']['crashes']} va chạm trên {mine['chosen']['n']} mẫu, so với {mine['baseline']['crashes']} baseline. Đây là kết quả khái quát tốt trên dải đã chọn, không phải một hazard còn đánh bại bản sửa. Không kết luận rủi ro bằng 0: cận Wilson vẫn là {sci(mine['chosen']['hi'])}. Bước sau nên thử dự đoán vùng chiếm chỗ ngang của xe đạp trong 1–2 s, TTC theo hộp chuyển động và giới hạn gia tốc, đồng thời đánh giá TG để tránh dời lỗi sang tông đuôi; quyết định bằng TRAIN mới thay vì chọn lại trên TEST đang báo cáo.", "",
              "Chưa thu bản ghi tự lái của người dùng; không khẳng định một người đã tránh được. Kết luận tránh được trong bài này đến từ oracle có quy tắc cụ thể, không phải thử lái thủ công.", "",
              "## Kiểm tra và tái lập", "",
              "31 kiểm thử TODO và 10 kiểm thử parity Python/JavaScript đạt. Xem `evidence/validation.txt` cho lệnh và kết quả. Evidence chính thức: world, replay, mc, hunt, cloud, estimate, fix, mine, viewer; `review.html`, `review-data.js`, `review-scenes.json` và ảnh là công cụ xem/bằng chứng bổ sung. Các probe thiết kế hazard không ghi đè các số chính thức.", ""]
    (ROOT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("REPORT.md generated from full-budget evidence")


if __name__ == "__main__":
    main()
